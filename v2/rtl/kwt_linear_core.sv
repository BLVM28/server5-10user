// SPDX-License-Identifier: MIT
// Fixed 99x64 * 64x256 + bias, 8 output lanes. All addresses are byte addresses.
// MEM_BASE/MEM_BYTES must name an integration-approved, CPU-accessible region.
// MEM_BYTES=0 deliberately rejects tasks; no assumed platform SRAM address.
module kwt_linear_core #(
  parameter [31:0] MEM_BASE=32'h0, MEM_BYTES=32'h0,
  parameter integer W_BANK_AW=7,
  parameter integer PACK_LOW_FIRST=1
) (
  input wire clk,rst_n,
  input wire task_valid, output wire task_ready,
  input wire [31:0] task_x,task_w,task_b,task_y,
  input wire [3:0] task_layer,
  output wire done_valid, input wire done_ready,
  output reg [31:0] status,sat_count,core_cycles,
  output wire busy,
  output reg mem_valid, input wire mem_ready,
  output reg [31:0] mem_addr,mem_wdata, output reg mem_read,
  input wire ret_valid, output reg ret_ready,
  input wire [31:0] ret_rdata, input wire ret_err
);
  localparam [4:0] IDLE=0,CHECK=1,X_REQ=2,X_WAIT=3,X_LOW=4,X_HIGH=5,
    W_REQ=6,W_WAIT=7,W_STORE=8,B_REQ=9,B_WAIT=10,INIT=11,FEED=12,
    DRAIN=13,Y_REQ=14,Y_WAIT=15,COMPLETE=16;
  reg [4:0] state;
  reg [31:0] xb,wb,bb,yb,load_word;
  reg [3:0] layer;
  reg [11:0] xword;
  reg [7:0] wword;
  reg [2:0] bword;
  reg [1:0] yword;
  reg [4:0] group_n;
  reg [6:0] row_m,issue_k;
  localparam [1:0] PREF_IDLE=0,PREF_INIT=1,PREF_FEED=2,PREF_DRAIN=3;
  reg [1:0] prefetch_state;
  reg [6:0] prefetch_row;
  reg [255:0] biases;
  reg [127:0] y_hold;
  wire [31:0] canonical_word=PACK_LOW_FIRST ? load_word : {load_word[15:0],load_word[31:16]};
  wire [31:0] output_word=y_hold[32*yword+:32];
  wire x_wr=rst_n && (state==X_LOW || state==X_HIGH);
  wire [12:0] x_wa={xword,1'b0} + (state==X_HIGH ? 13'd1 : 13'd0);
  wire [15:0] x_wd=state==X_LOW ? canonical_word[15:0] : canonical_word[31:16];
  // Existing y_hold and the MAC response registers form a two-slot handoff.
  // Only the writer owns ICB; next-row compute uses the resident X/W SRAMs.
  wire compute_clear=state==IDLE || state==COMPLETE ||
                     (state==Y_WAIT && ret_valid && ret_err);
  wire operand_read=rst_n && !compute_clear &&
                    (state==FEED || prefetch_state==PREF_FEED);
  wire [6:0] read_row=prefetch_state==PREF_FEED ? prefetch_row : row_m;
  wire [12:0] x_ra={read_row,6'b0}+{6'b0,issue_k};
  wire x_rv,w_rv; wire [15:0] x_rd; wire [127:0] w_rd;
  wire mac_cr,mac_pr,mac_ov; wire [127:0] mac_y; wire [7:0] mac_sat;
  wire [319:0] mac_acc;
  assign task_ready=rst_n && state==IDLE;
  assign done_valid=rst_n && state==COMPLETE;
  assign busy=state!=IDLE;

  function automatic range_ok(input [31:0] base,input [31:0] bytes);
    reg [32:0] finish,limit;
    begin
      finish={1'b0,base}+{1'b0,bytes};
      limit={1'b0,MEM_BASE}+{1'b0,MEM_BYTES};
      range_ok=(MEM_BYTES!=0) && base[1:0]==0 && base>=MEM_BASE &&
        finish<=limit && finish<=33'h100000000 && limit<=33'h100000000;
    end
  endfunction
  function automatic overlap(input [31:0] a,input [31:0] alen,input [31:0] b,input [31:0] blen);
    begin overlap=({1'b0,a}<({1'b0,b}+{1'b0,blen})) &&
                  ({1'b0,b}<({1'b0,a}+{1'b0,alen})); end
  endfunction
  function automatic [31:0] count_bits(input [7:0] flags);
    integer j;
    begin count_bits=0;for(j=0;j<8;j=j+1) count_bits=count_bits+flags[j];end
  endfunction
  wire config_ok=range_ok(xb,12672)&&range_ok(wb,32768)&&range_ok(bb,1024)&&range_ok(yb,50688)&&
    !overlap(xb,12672,wb,32768)&&!overlap(xb,12672,bb,1024)&&!overlap(xb,12672,yb,50688)&&
    !overlap(wb,32768,bb,1024)&&!overlap(wb,32768,yb,50688)&&!overlap(bb,1024,yb,50688);

  kwt_x_buffer xbuffer(.clk(clk),.rst_n(rst_n),.wr_en(x_wr),.wr_addr(x_wa),
    .wr_data(x_wd),.rd_en(operand_read),.rd_addr(x_ra),.rd_valid(x_rv),.rd_data(x_rd));
  kwt_w_panel #(.BANK_AW(W_BANK_AW)) wbuffer(.clk(clk),.rst_n(rst_n),
    .wr_en(rst_n && state==W_STORE),.wr_pair(wword[1:0]),.wr_k(wword[7:2]),
    .wr_data(canonical_word),.rd_en(operand_read),.rd_k(issue_k[5:0]),.rd_valid(w_rv),.rd_data(w_rd));
  kwt_mac8 mac(.clk(clk),.rst_n(rst_n),.clear(compute_clear),
    .cmd_valid(state==INIT || prefetch_state==PREF_INIT),.cmd_ready(mac_cr),
    .biases(biases),.pair_valid(x_rv&&w_rv),.pair_ready(mac_pr),.x(x_rd),.weights(w_rd),
    .out_valid(mac_ov),.out_ready(state==DRAIN),.results(mac_y),.accumulators(mac_acc),.saturated(mac_sat));

  always @* begin
    mem_valid=0;mem_addr=0;mem_wdata=0;mem_read=1;ret_ready=0;
    case(state)
      X_REQ: begin mem_valid=rst_n;mem_addr=xb+({20'b0,xword}<<2);end
      W_REQ: begin mem_valid=rst_n;
        mem_addr=wb+({26'b0,wword[7:2]}<<9)+({27'b0,group_n}<<4)+({30'b0,wword[1:0]}<<2);end
      B_REQ: begin mem_valid=rst_n;mem_addr=bb+({27'b0,group_n}<<5)+({29'b0,bword}<<2);end
      Y_REQ: begin mem_valid=rst_n;mem_read=0;
        mem_addr=yb+({25'b0,row_m}<<9)+({27'b0,group_n}<<4)+({30'b0,yword}<<2);
        mem_wdata=PACK_LOW_FIRST ? output_word : {output_word[15:0],output_word[31:16]};end
      X_WAIT,W_WAIT,B_WAIT,Y_WAIT: ret_ready=rst_n;
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=IDLE;xb<=0;wb<=0;bb<=0;yb<=0;layer<=0;load_word<=0;
      xword<=0;wword<=0;bword<=0;yword<=0;group_n<=0;row_m<=0;issue_k<=0;
      biases<=0;y_hold<=0;status<=0;sat_count<=0;core_cycles<=0;
      prefetch_state<=PREF_IDLE;prefetch_row<=0;
    end else begin
      if(state!=IDLE && state!=COMPLETE) core_cycles<=core_cycles+1'b1;
      if(compute_clear)prefetch_state<=PREF_IDLE;
      else case(prefetch_state)
        PREF_INIT: if(mac_cr)begin issue_k<=0;prefetch_state<=PREF_FEED;end
        PREF_FEED: if(issue_k==63)prefetch_state<=PREF_DRAIN;
                   else issue_k<=issue_k+1'b1;
        default: begin end
      endcase
      case(state)
        IDLE: if(task_valid) begin
          xb<=task_x;wb<=task_w;bb<=task_b;yb<=task_y;layer<=task_layer;
          status<=0;sat_count<=0;core_cycles<=0;
          group_n<=0;row_m<=0;xword<=0;wword<=0;bword<=0;yword<=0;issue_k<=0;
          state<=CHECK;
        end
        CHECK: if(layer>=12) begin status<=4;state<=COMPLETE;end
          else if(!config_ok) begin status<=1;state<=COMPLETE;end
          else state<=X_REQ;
        X_REQ: if(mem_valid&&mem_ready) state<=X_WAIT;
        X_WAIT: if(ret_valid) begin
          if(ret_err) begin status<=2;state<=COMPLETE;end
          else begin load_word<=ret_rdata;state<=X_LOW;end
        end
        X_LOW: state<=X_HIGH;
        X_HIGH: if(xword==3167) begin wword<=0;state<=W_REQ;end
          else begin xword<=xword+1'b1;state<=X_REQ;end
        W_REQ: if(mem_valid&&mem_ready) state<=W_WAIT;
        W_WAIT: if(ret_valid) begin
          if(ret_err) begin status<=2;state<=COMPLETE;end
          else begin load_word<=ret_rdata;state<=W_STORE;end
        end
        W_STORE: if(wword==255) begin bword<=0;state<=B_REQ;end
          else begin wword<=wword+1'b1;state<=W_REQ;end
        B_REQ: if(mem_valid&&mem_ready) state<=B_WAIT;
        B_WAIT: if(ret_valid) begin
          if(ret_err) begin status<=2;state<=COMPLETE;end
          else begin
            biases[32*bword+:32]<=ret_rdata;
            if(bword==7) begin row_m<=0;state<=INIT;end
            else begin bword<=bword+1'b1;state<=B_REQ;end
          end
        end
        INIT: if(mac_cr) begin issue_k<=0;state<=FEED;end
        FEED: if(issue_k==63) state<=DRAIN;else issue_k<=issue_k+1'b1;
        DRAIN: if(mac_ov) begin
          y_hold<=mac_y;sat_count<=sat_count+count_bits(mac_sat);yword<=0;state<=Y_REQ;
          if(row_m!=98)begin prefetch_row<=row_m+1'b1;prefetch_state<=PREF_INIT;end
          else prefetch_state<=PREF_IDLE;
        end
        Y_REQ: if(mem_valid&&mem_ready) state<=Y_WAIT;
        Y_WAIT: if(ret_valid) begin
          if(ret_err) begin status<=3;state<=COMPLETE;end
          else if(yword!=3) begin yword<=yword+1'b1;state<=Y_REQ;end
          else if(row_m!=98) begin row_m<=row_m+1'b1;state<=DRAIN;end
          else if(group_n!=31) begin group_n<=group_n+1'b1;wword<=0;state<=W_REQ;end
          else state<=COMPLETE;
        end
        COMPLETE: if(done_ready) state<=IDLE;
        default: begin status<=32'hff;state<=COMPLETE;end
      endcase
    end
  end
endmodule

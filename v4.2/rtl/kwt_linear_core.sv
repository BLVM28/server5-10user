// SPDX-License-Identifier: MIT
// 99x64 by 64x256. Independent compute and DMA jobs use opposite pages.
module kwt_linear_core #(
  parameter [31:0] MEM_BASE=0,MEM_BYTES=0,
  parameter integer W_BANK_AW=7,PACK_LOW_FIRST=1,STRIPES=4
)(
  input wire clk,rst_n,task_valid,output wire task_ready,
  input wire [31:0] task_x,task_w,task_b,task_y,input wire [3:0] task_layer,input wire task_compact,task_fast,task_precision,input wire [11:0] task_scales,
  output wire done_valid,input wire done_ready,output reg [31:0] status,sat_count,core_cycles,
  output wire busy,mem_valid,input wire mem_ready,output wire [31:0] mem_addr,mem_wdata,
  output wire mem_read,input wire ret_valid,output wire ret_ready,input wire [31:0] ret_rdata,input wire ret_err
);
  localparam IDLE=0,CHECK=1,X_START=2,X_WAIT=3,FIRST_START=4,FIRST_WAIT=5,
             BEGIN_TILE=6,NEXT_START=7,NEXT_WAIT=8,PREV_START=9,PREV_WAIT=10,
             JOIN_TILE=11,LAST_START=12,LAST_WAIT=13,COMPLETE=14;
  reg [3:0] state;
  reg [31:0] xb,wb,bb,yb;
  reg [3:0] layer;
  reg compact,fast,precision;reg [11:0] scales;
  reg [4:0] group_n;
  wire dma_done;
  wire [1:0] dma_error;
  wire dma_failed=dma_done && dma_error!=0;
  wire dma_start=state==X_START || state==FIRST_START || state==NEXT_START || state==PREV_START || state==LAST_START;
  wire [1:0] dma_job=state==X_START ? 0 : ((state==PREV_START || state==LAST_START) ? 2 : 1);
  wire [4:0] dma_group=state==NEXT_START ? group_n+1'b1 : state==PREV_START ? group_n-1'b1 : group_n;
  wire x_write,w_write,b_write,dma_page,y_read;wire [1:0] x_stripe;wire [5:0] x_tile;wire [4:0] x_pair;
  wire [31:0] canonical;wire [7:0] w_index;wire [2:0] b_index;wire [6:0] y_rd_row;
  wire [127:0] y_vector;
  wire operand_read,x_rv,mac_pr,compute_done,result_commit;wire [5:0] tile,k;
  wire [6:0] row_m;wire [16*STRIPES-1:0] xs;wire [127:0] result_y;wire [319:0] mac_acc;wire [7:0] sat;
  wire [1:0] w_valid;wire [127:0] wq[0:1];wire w_rv=w_valid[group_n[0]];
  reg [255:0] biases[0:1];
  assign task_ready=rst_n && state==IDLE;assign busy=state!=IDLE;assign done_valid=rst_n && state==COMPLETE;
  function automatic range_ok(input [31:0] a,n);
    reg [32:0] limit,finish;
    begin limit={1'b0,MEM_BASE}+{1'b0,MEM_BYTES};finish={1'b0,a}+{1'b0,n};
      range_ok=MEM_BYTES!=0 && a[1:0]==0 && a>=MEM_BASE && finish<=limit && limit<=33'h100000000;end
  endfunction
  function automatic overlap(input [31:0] a,alen,b,blen);
    begin overlap={1'b0,a}<({1'b0,b}+{1'b0,blen}) && {1'b0,b}<({1'b0,a}+{1'b0,alen});end
  endfunction
  wire [31:0] xbytes=precision ? 16384 : (fast ? 6732 : 12672), wbytes=precision ? 65536 : (fast ? 16512 : 32768);
  wire [31:0] ybytes=precision ? 65536 : (fast ? 27008 : (compact ? 51584 : 50688));
  wire config_ok=range_ok(xb,xbytes) && range_ok(wb,wbytes) && range_ok(bb,1024) && range_ok(yb,ybytes)
    && !overlap(xb,xbytes,wb,wbytes) && !overlap(xb,xbytes,bb,1024) && !overlap(xb,xbytes,yb,ybytes)
    && !overlap(wb,wbytes,bb,1024) && !overlap(wb,wbytes,yb,ybytes) && !overlap(bb,1024,yb,ybytes);
  wire compute_clear=state==IDLE || state==COMPLETE || dma_failed;
  kwt_tile_dma #(.PACK_LOW_FIRST(PACK_LOW_FIRST),.STRIPES(STRIPES)) dma(.clk(clk),.rst_n(rst_n),.start(dma_start),.job(dma_job),
    .group_index(dma_group),.xb(xb),.wb(wb),.bb(bb),.yb(yb),.compact(compact),.fast(fast),.precision(precision),.scales(scales),.done(dma_done),.error(dma_error),
    .mem_valid(mem_valid),.mem_read(mem_read),.mem_addr(mem_addr),.mem_wdata(mem_wdata),.mem_ready(mem_ready),
    .ret_valid(ret_valid),.ret_err(ret_err),.ret_rdata(ret_rdata),.ret_ready(ret_ready),
    .x_write(x_write),.x_stripe(x_stripe),.x_tile(x_tile),.x_pair(x_pair),.canonical(canonical),
    .w_write(w_write),.b_write(b_write),.page(dma_page),.w_index(w_index),.b_index(b_index),
    .y_read(y_read),.y_rd_addr(y_rd_row),.y_vector(y_vector));
  kwt_x_buffer #(.STRIPES(STRIPES)) xbuffer(.clk(clk),.rst_n(rst_n),.wr_en(x_write),.wr_stripe(x_stripe),.wr_tile(x_tile),
    .wr_pair(x_pair),.wr_data(canonical),.rd_en(operand_read),.rd_tile(tile),.rd_k(k),.rd_valid(x_rv),.rd_data(xs));
  genvar p;
  generate for(p=0;p<2;p=p+1)begin: pages
    kwt_w_panel #(.BANK_AW(W_BANK_AW)) weights(.clk(clk),.rst_n(rst_n),.wr_en(w_write && dma_page==p),
      .wr_page(1'b0),.wr_pair(w_index[1:0]),.wr_k(w_index[7:2]),.wr_data(canonical),
      .rd_en(operand_read && group_n[0]==p),.rd_page(1'b0),.rd_k(k),.rd_valid(w_valid[p]),.rd_data(wq[p]));
    always @(posedge clk) if(b_write && dma_page==p)biases[p][b_index*32+:32]<=ret_rdata;
  end endgenerate
  kwt_tile_compute #(.STRIPES(STRIPES)) compute(.clk(clk),.rst_n(rst_n),.start(state==BEGIN_TILE),.clear(compute_clear),
    .biases(biases[group_n[0]]),.rd_en(operand_read),.tile(tile),.k(k),.pair_valid(x_rv&&w_rv),
    .xs(xs),.weights(wq[group_n[0]]),.pair_ready(mac_pr),.commit(result_commit),.row(row_m),
    .y(result_y),
`ifndef SYNTHESIS
    .acc(mac_acc),
`endif
    .saturated(sat),.done(compute_done));
  kwt_result_pages outputs(.clk(clk),.wr_en(result_commit),.wr_page(group_n[0]),.wr_row(row_m),.wr_data(result_y),
    .rd_en(y_read),.rd_page(dma_page),.rd_row(y_rd_row),.rd_data(y_vector));
  function automatic [3:0] pop8(input [7:0] bits);
    integer i;begin pop8=0;for(i=0;i<8;i=i+1)pop8=pop8+bits[i];end
  endfunction
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n) begin state<=IDLE;group_n<=0;core_cycles<=0;sat_count<=0;status<=0;
      xb<=0;wb<=0;bb<=0;yb<=0;layer<=0;compact<=0;fast<=0;precision<=0;scales<=0;end
    else begin
      if(state!=IDLE && state!=COMPLETE)core_cycles<=core_cycles+1'b1;
      if(result_commit)sat_count<=sat_count+pop8(sat);
      if(dma_failed)begin status<={30'd0,dma_error};state<=COMPLETE;end
      else case(state)
        IDLE: if(task_valid)begin
          xb<=task_x;wb<=task_w;bb<=task_b;yb<=task_y;layer<=task_layer;compact<=task_compact;fast<=task_fast;precision<=task_precision;scales<=task_scales;
          group_n<=0;core_cycles<=0;sat_count<=0;status<=0;state<=CHECK;
        end
        CHECK: if(layer>=12)begin status<=4;state<=COMPLETE;end
               else if(!config_ok)begin status<=1;state<=COMPLETE;end else state<=X_START;
        X_START: state<=X_WAIT;
        X_WAIT: if(dma_done)state<=FIRST_START;
        FIRST_START:state<=FIRST_WAIT;
        FIRST_WAIT:if(dma_done)state<=BEGIN_TILE;
        BEGIN_TILE:state<=group_n==31 ? PREV_START : NEXT_START;
        NEXT_START:state<=NEXT_WAIT;
        NEXT_WAIT:if(dma_done)state<=group_n==0 ? JOIN_TILE : PREV_START;
        PREV_START:state<=PREV_WAIT;
        PREV_WAIT:if(dma_done)state<=JOIN_TILE;
        JOIN_TILE:if(compute_done)begin
          if(group_n==31)state<=LAST_START;
          else begin group_n<=group_n+1'b1;state<=BEGIN_TILE;end
        end
        LAST_START:state<=LAST_WAIT;
        LAST_WAIT:if(dma_done)state<=COMPLETE;
        COMPLETE:if(done_ready)state<=IDLE;
        default:begin status<=32'hff;state<=COMPLETE;end
      endcase
    end
  end
endmodule

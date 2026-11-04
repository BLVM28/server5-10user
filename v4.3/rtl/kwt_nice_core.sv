// SPDX-License-Identifier: MIT
// Proposed application ABI: custom3(0x7b), funct7=0x40, funct3=6 (xd,xs1,!xs2).
// rs1: descriptor pointer. Descriptor: magic,format,layer,X,W,b,Y,reserved.
// One long instruction returns only after all output writes are acknowledged.
module kwt_nice_core #(
  parameter [31:0] MEM_BASE=0,MEM_BYTES=0,
  parameter integer W_BANK_AW=7,PACK_LOW_FIRST=1
) (
  input wire nice_clk,nice_rst_n,
  output wire nice_active,nice_mem_holdup,
  input wire nice_req_valid, output wire nice_req_ready,
  input wire [31:0] nice_req_inst,nice_req_rs1,nice_req_rs2,
  output wire nice_rsp_valid, input wire nice_rsp_ready,
  output reg [31:0] nice_rsp_rdat, output reg nice_rsp_err,
  output wire nice_icb_cmd_valid, input wire nice_icb_cmd_ready,
  output wire [31:0] nice_icb_cmd_addr, output wire nice_icb_cmd_read,
  output wire [31:0] nice_icb_cmd_wdata, output wire [1:0] nice_icb_cmd_size,
  input wire nice_icb_rsp_valid, output wire nice_icb_rsp_ready,
  input wire [31:0] nice_icb_rsp_rdata, input wire nice_icb_rsp_err
);
  localparam [2:0] IDLE=0,FETCH=1,FETCH_WAIT=2,VALIDATE=3,START=4,RUN=5,RESPONSE=6;
  reg [2:0] state,word_index;
  reg [31:0] descriptor,words[0:7];
  wire c_valid,c_ready,c_done,c_ret_ready,c_mem_valid,c_mem_ready,c_mem_read;
  wire [31:0] c_status,c_sat,c_cycles,c_mem_addr,c_mem_wdata;
  wire master_ready,master_ret_valid,master_ret_err,master_idle;
  wire [31:0] master_rdata;
  wire route_core=(state==RUN);
  wire master_req_valid=route_core?c_mem_valid:(state==FETCH);
  wire master_ret_ready=route_core?c_ret_ready:(state==FETCH_WAIT);
  wire [31:0] master_addr=route_core?c_mem_addr:(descriptor+{27'b0,word_index,2'b0});
  assign c_mem_ready=route_core&&master_ready;
  assign c_valid=(state==START);
  assign nice_req_ready=nice_rst_n&&state==IDLE;
  assign nice_rsp_valid=nice_rst_n&&state==RESPONSE;
  assign nice_active=state!=IDLE;
  assign nice_mem_holdup=nice_rst_n&&state!=IDLE&&state!=RESPONSE;
  function automatic in_region(input [31:0] base,input [31:0] bytes);
    reg [32:0] limit,finish;
    begin
      limit={1'b0,MEM_BASE}+{1'b0,MEM_BYTES};finish={1'b0,base}+{1'b0,bytes};
      in_region=MEM_BYTES!=0 && base[1:0]==0 && base>=MEM_BASE &&
        finish<=limit && limit<=33'h100000000 && finish<=33'h100000000;
    end
  endfunction
  function automatic desc_overlap(input [31:0] base,input [31:0] bytes);
    begin desc_overlap=({1'b0,descriptor} < ({1'b0,base}+{1'b0,bytes})) &&
        ({1'b0,base}<({1'b0,descriptor}+33'd32));end
  endfunction

  kwt43_core #(.MEM_BASE(MEM_BASE),.MEM_BYTES(MEM_BYTES),.PACK_LOW_FIRST(PACK_LOW_FIRST)) core(.clk(nice_clk),.rst_n(nice_rst_n),
    .task_valid(c_valid),.task_ready(c_ready),.task_x(words[3]),.task_w(words[4]),
    .task_b(words[5]),.task_y(words[6]),.task_layer(words[2][3:0]),.task_scales(words[7][11:0]),
    .done_valid(c_done),.done_ready(state==RUN),.status(c_status),.sat_count(c_sat),
    .core_cycles(c_cycles),.busy(),.mem_valid(c_mem_valid),.mem_ready(c_mem_ready),
    .mem_addr(c_mem_addr),.mem_wdata(c_mem_wdata),.mem_read(c_mem_read),
    .ret_valid(route_core&&master_ret_valid),.ret_ready(c_ret_ready),
    .ret_rdata(master_rdata),.ret_err(master_ret_err));
  kwt43_icb_master master(.clk(nice_clk),.rst_n(nice_rst_n),
    .req_valid(master_req_valid),.req_ready(master_ready),.req_addr(master_addr),
    .req_wdata(route_core?c_mem_wdata:32'b0),.req_read(route_core?c_mem_read:1'b1),
    .ret_valid(master_ret_valid),.ret_ready(master_ret_ready),.ret_rdata(master_rdata),
    .ret_err(master_ret_err),.cmd_valid(nice_icb_cmd_valid),.cmd_ready(nice_icb_cmd_ready),
    .cmd_addr(nice_icb_cmd_addr),.cmd_wdata(nice_icb_cmd_wdata),.cmd_read(nice_icb_cmd_read),
    .cmd_size(nice_icb_cmd_size),.rsp_valid(nice_icb_rsp_valid),.rsp_ready(nice_icb_rsp_ready),
    .rsp_rdata(nice_icb_rsp_rdata),.rsp_err(nice_icb_rsp_err),.idle(master_idle));
  integer i;
  always @(posedge nice_clk or negedge nice_rst_n) begin
    if(!nice_rst_n) begin
      state<=IDLE;word_index<=0;descriptor<=0;nice_rsp_rdat<=0;nice_rsp_err<=0;
      for(i=0;i<8;i=i+1) words[i]<=0;
    end else case(state)
      IDLE: if(nice_req_valid) begin
        nice_rsp_rdat<=0;nice_rsp_err<=0;descriptor<=nice_req_rs1;word_index<=0;
        if(nice_req_inst[6:0]!=7'h7b || nice_req_inst[31:25]!=7'h40 ||
           nice_req_inst[14:12]!=3'b110 || nice_req_inst[24:20]!=0) begin
          nice_rsp_rdat<=32'h10;nice_rsp_err<=1;state<=RESPONSE;
        end else if(!in_region(nice_req_rs1,32)) begin
          nice_rsp_rdat<=32'h11;nice_rsp_err<=1;state<=RESPONSE;
        end else state<=FETCH;
      end
      FETCH: if(master_ready) state<=FETCH_WAIT;
      FETCH_WAIT: if(master_ret_valid) begin
        if(master_ret_err) begin nice_rsp_rdat<=32'h13;nice_rsp_err<=1;state<=RESPONSE;end
        else begin
          words[word_index]<=master_rdata;
          if(word_index==7) state<=VALIDATE;
          else begin word_index<=word_index+1'b1;state<=FETCH;end
        end
      end
      VALIDATE: if(words[0]!=32'h3154574b || words[1]!=32'h00010004 ||
          words[7][31:12]!=0 || words[7][3:0]<1 || words[7][3:0]>5 || words[7][7:4]<3 || words[7][7:4]>5 || words[7][11:8]>5)begin
        nice_rsp_rdat<=32'h12;nice_rsp_err<=1;state<=RESPONSE;
      end else if(words[2]>=12)begin nice_rsp_rdat<=4;nice_rsp_err<=1;state<=RESPONSE;
      end else if(desc_overlap(words[3],16384)||desc_overlap(words[4],65536)||
          desc_overlap(words[5],1024)||desc_overlap(words[6],65536))begin
        nice_rsp_rdat<=1;nice_rsp_err<=1;state<=RESPONSE;
      end else state<=START;
      START: if(c_ready) state<=RUN;
      RUN: if(c_done) begin nice_rsp_rdat<=c_status;nice_rsp_err<=c_status!=0;state<=RESPONSE;end
      RESPONSE: if(nice_rsp_ready) state<=IDLE;
      default: begin nice_rsp_rdat<=32'hff;nice_rsp_err<=1;state<=RESPONSE;end
    endcase
  end
endmodule

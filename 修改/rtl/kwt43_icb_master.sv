// SPDX-License-Identifier: MIT
// 单笔在途。命令和响应均经寄存后跨过接口。
module kwt43_icb_master (
  input wire clk,rst_n,req_valid,output wire req_ready,
  input wire [31:0] req_addr,req_wdata,input wire req_read,
  output wire ret_valid,input wire ret_ready,output wire [31:0] ret_rdata,
  output wire ret_err,cmd_valid,input wire cmd_ready,
  output wire [31:0] cmd_addr,cmd_wdata,output wire cmd_read,output wire [1:0] cmd_size,
  input wire rsp_valid,output wire rsp_ready,input wire [31:0] rsp_rdata,input wire rsp_err,
  output wire idle
);
  localparam [3:0] EMPTY=4'b0001, SEND=4'b0010, WAIT_RSP=4'b0100, HOLD_RSP=4'b1000;
  reg [3:0] state;
  reg [31:0] addr_q,data_q,response_q;
  reg read_q,error_q;
  assign req_ready=rst_n && state[0];
  assign cmd_valid=state[1];
  assign cmd_addr=addr_q;
  assign cmd_wdata=data_q;
  assign cmd_read=read_q;
  assign cmd_size=2'b10;
  wire external_command=cmd_valid && cmd_ready;
  // 提前给出 ready，兼容零周期应答并切开命令到应答的 ready 链。
  assign rsp_ready=state[1] || state[2];
  wire incoming=rsp_valid && rsp_ready;
  assign ret_valid=state[3];
  assign ret_rdata=response_q;
  assign ret_err=error_q;
  assign idle=state[0];
  wire accepted=req_valid && req_ready;
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) state<=EMPTY;
    else case (state)
      EMPTY: if (accepted) state <= SEND;
      SEND: if (external_command) state <= incoming ? HOLD_RSP : WAIT_RSP;
      WAIT_RSP: if (incoming) state <= HOLD_RSP;
      HOLD_RSP: if (ret_ready) state <= EMPTY;
      default: state <= EMPTY;
    endcase
  end
  always @(posedge clk) begin
    if(accepted)begin addr_q<=req_addr;data_q<=req_wdata;read_q<=req_read;end
    if(incoming)begin response_q<=rsp_rdata;error_q<=rsp_err;end
  end
endmodule

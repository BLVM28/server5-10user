// SPDX-License-Identifier: MIT
// One external transaction at a time. An unstalled request goes straight to
// ICB. A skid register owns its pins if the slave stalls; responses likewise.
module kwt_icb_master (
  input wire clk,rst_n,req_valid, output wire req_ready,
  input wire [31:0] req_addr,req_wdata,input wire req_read,
  output wire ret_valid,input wire ret_ready,output wire [31:0] ret_rdata,
  output wire ret_err,cmd_valid,input wire cmd_ready,
  output wire [31:0] cmd_addr,cmd_wdata,output wire cmd_read,output wire [1:0] cmd_size,
  input wire rsp_valid,output wire rsp_ready,input wire [31:0] rsp_rdata,input wire rsp_err,
  output wire idle
);
  localparam IDLE=2'd0, SEND=2'd1, WAIT_RSP=2'd2, HOLD_RSP=2'd3;
  reg [1:0] state;
  reg [31:0] addr_q,data_q,rdata_q;
  reg read_q,error_q;
  assign idle=state==IDLE;
  assign req_ready=rst_n && idle;
  assign cmd_valid=rst_n && ((idle && req_valid) || state==SEND);
  assign cmd_addr=state==SEND ? addr_q : req_addr;
  assign cmd_wdata=state==SEND ? data_q : req_wdata;
  assign cmd_read=state==SEND ? read_q : req_read;
  assign cmd_size=2'd2;
  assign rsp_ready=rst_n && (state==WAIT_RSP || (cmd_valid && cmd_ready));
  wire incoming=rsp_valid && rsp_ready;
  assign ret_valid=rst_n && (state==HOLD_RSP || incoming);
  assign ret_rdata=state==HOLD_RSP ? rdata_q : rsp_rdata;
  assign ret_err=state==HOLD_RSP ? error_q : rsp_err;
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) state<=IDLE;
    else if(incoming) state<=ret_ready ? IDLE : HOLD_RSP;
    else case(state)
      IDLE: if(req_valid) state<=cmd_ready ? WAIT_RSP : SEND;
      SEND: if(cmd_ready) state<=WAIT_RSP;
      HOLD_RSP: if(ret_ready) state<=IDLE;
      default: state<=WAIT_RSP;
    endcase
  end
  always @(posedge clk) begin
    if(req_ready && req_valid && !cmd_ready) begin
      addr_q<=req_addr;data_q<=req_wdata;read_q<=req_read;
    end
    if(incoming && !ret_ready) begin rdata_q<=rsp_rdata;error_q<=rsp_err;end
  end
endmodule

// SPDX-License-Identifier: MIT
// One outstanding transaction. Both reads and writes await a response.
// Handles a response concurrent with command acceptance as well as delayed ones.
module kwt_icb_master (
  input wire clk, rst_n,
  input wire req_valid, output wire req_ready,
  input wire [31:0] req_addr, req_wdata,
  input wire req_read,
  output wire ret_valid, input wire ret_ready,
  output reg [31:0] ret_rdata, output reg ret_err,
  output wire cmd_valid, input wire cmd_ready,
  output reg [31:0] cmd_addr, cmd_wdata,
  output reg cmd_read, output wire [1:0] cmd_size,
  input wire rsp_valid, output wire rsp_ready,
  input wire [31:0] rsp_rdata, input wire rsp_err,
  output wire idle
);
  localparam [1:0] IDLE=0, SEND=1, WAIT_RSP=2, RETURN_RSP=3;
  reg [1:0] state;
  assign req_ready=rst_n && state==IDLE;
  assign cmd_valid=rst_n && state==SEND;
  assign cmd_size=2'b10;
  assign rsp_ready=rst_n && ((state==WAIT_RSP) || ((state==SEND)&&cmd_ready));
  assign ret_valid=rst_n && state==RETURN_RSP;
  assign idle=state==IDLE;
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      state<=IDLE; cmd_addr<=0; cmd_wdata<=0; cmd_read<=1;
      ret_rdata<=0; ret_err<=0;
    end else case(state)
      IDLE: if(req_valid) begin
        cmd_addr<=req_addr; cmd_wdata<=req_wdata; cmd_read<=req_read; state<=SEND;
      end
      SEND: if(cmd_ready) begin
        if(rsp_valid) begin ret_rdata<=rsp_rdata; ret_err<=rsp_err; state<=RETURN_RSP; end
        else state<=WAIT_RSP;
      end
      WAIT_RSP: if(rsp_valid) begin ret_rdata<=rsp_rdata; ret_err<=rsp_err; state<=RETURN_RSP; end
      RETURN_RSP: if(ret_ready) state<=IDLE;
    endcase
  end
endmodule

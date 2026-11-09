// SPDX-License-Identifier: MIT
// Eight credits cover queued commands, external requests and buffered replies.
// A two-entry command queue and an eight-entry reply queue register both bus
// directions. The target returns one ordered reply per accepted command.
module kwt43_icb_master (
  input wire clk,rst_n,req_valid,output wire req_ready,
  input wire [31:0] req_addr,req_wdata,input wire req_read,
  output wire ret_valid,input wire ret_ready,output wire [31:0] ret_rdata,
  output wire ret_err,cmd_valid,input wire cmd_ready,
  output wire [31:0] cmd_addr,cmd_wdata,output wire cmd_read,output wire [1:0] cmd_size,
  input wire rsp_valid,output wire rsp_ready,input wire [31:0] rsp_rdata,input wire rsp_err,
  output wire idle
);
  reg [3:0] used, issued;
  wire command_room, reply_room;
  wire credit = used < 4'd8;
  wire response_expected = issued != 0 || cmd_valid;
  wire take_request = req_valid && req_ready;
  wire send_command = cmd_valid && cmd_ready;
  wire take_reply = rsp_valid && rsp_ready;
  wire deliver_reply = ret_valid && ret_ready;

  assign req_ready = credit && command_room;
  assign rsp_ready = reply_room && response_expected;
  assign cmd_size = 2'b10;
  assign idle = used == 0;

  kwt44_fifo #(.WIDTH(65), .DEPTH(2)) commands(
    .clk(clk), .rst_n(rst_n),
    .push_valid(req_valid && credit), .push_ready(command_room),
    .push_data({req_read,req_addr,req_wdata}),
    .pop_valid(cmd_valid), .pop_ready(cmd_ready), .pop_data({cmd_read,cmd_addr,cmd_wdata})
  );
  kwt44_fifo #(.WIDTH(33), .DEPTH(8)) replies(
    .clk(clk), .rst_n(rst_n),
    .push_valid(rsp_valid && response_expected), .push_ready(reply_room),
    .push_data({rsp_err,rsp_rdata}),
    .pop_valid(ret_valid), .pop_ready(ret_ready), .pop_data({ret_err,ret_rdata})
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      used <= 0;
      issued <= 0;
    end else begin
      case ({take_request,deliver_reply})
        2'b10: used <= used + 1'b1;
        2'b01: used <= used - 1'b1;
        default: ;
      endcase
      case ({send_command,take_reply})
        2'b10: issued <= issued + 1'b1;
        2'b01: issued <= issued - 1'b1;
        default: ;
      endcase
    end
  end
endmodule

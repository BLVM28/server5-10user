// SPDX-License-Identifier: MIT
// Rebuilt from the documented S1 contract; not a copy of the missing S1 source.
module kwt_dot64 (
  input wire clk, rst_n,
  input wire cmd_valid, output wire cmd_ready,
  input wire signed [31:0] cmd_bias,
  input wire pair_valid, output wire pair_ready,
  input wire signed [15:0] pair_x, pair_w,
  output wire out_valid, input wire out_ready,
  output reg signed [15:0] out_y,
  output reg signed [39:0] out_acc,
  output reg out_saturated, output wire busy
);
  localparam [1:0] IDLE=0, RUN=1, ROUND=2, RESPONSE=3;
  reg [1:0] state;
  reg [6:0] received;
  reg signed [39:0] acc;
  wire mul_valid, mul_last;
  wire signed [31:0] product;
  wire signed [15:0] quant_y;
  wire quant_sat;
  assign cmd_ready = rst_n && state==IDLE;
  assign pair_ready = rst_n && state==RUN && received<64;
  assign out_valid = rst_n && state==RESPONSE;
  assign busy = state!=IDLE;
  kwt_mul16_pipe mul(.clk(clk),.rst_n(rst_n),
    .in_valid(pair_valid && pair_ready),.in_last(received==63),
    .in_x(pair_x),.in_w(pair_w),.out_valid(mul_valid),
    .out_last(mul_last),.out_product(product));
  kwt_quantize quant(.acc(acc),.y(quant_y),.saturated(quant_sat));
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; received<=0; acc<=0;
      out_y<=0; out_acc<=0; out_saturated<=0;
    end else case(state)
      IDLE: if(cmd_valid && cmd_ready) begin
        acc <= {{8{cmd_bias[31]}},cmd_bias}; received<=0; state<=RUN;
      end
      RUN: begin
        if(pair_valid && pair_ready) received<=received+1'b1;
        if(mul_valid) begin
          acc <= acc + {{8{product[31]}},product};
          if(mul_last) state<=ROUND;
        end
      end
      ROUND: begin out_y<=quant_y; out_acc<=acc; out_saturated<=quant_sat; state<=RESPONSE; end
      RESPONSE: if(out_ready) state<=IDLE;
      default: state<=IDLE;
    endcase
  end
endmodule

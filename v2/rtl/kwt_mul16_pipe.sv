// SPDX-License-Identifier: MIT
// V2: operand register -> two parallel partial products -> exact recombine.
// Initiation interval remains one clock. Valid/last travel with the data.
module kwt_mul16_pipe (
  input wire clk, rst_n, clear, in_valid, in_last,
  input wire signed [15:0] in_x, in_w,
  output reg out_valid, out_last,
  output reg signed [31:0] out_product
);
  reg v_operand, v_partial, last_operand, last_partial;
  reg signed [15:0] x_operand, w_operand;
  reg signed [24:0] partial_low;
  reg signed [23:0] partial_high;
  wire signed [8:0] w_low = $signed({1'b0,w_operand[7:0]});
  wire signed [7:0] w_high = $signed(w_operand[15:8]);
  wire signed [31:0] low_extended = {{7{partial_low[24]}},partial_low};
  wire signed [31:0] high_shifted = {partial_high,8'b0};
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      v_operand<=0;v_partial<=0;out_valid<=0;
      last_operand<=0;last_partial<=0;out_last<=0;
      x_operand<=0;w_operand<=0;partial_low<=0;partial_high<=0;out_product<=0;
    end
    else if(clear) begin
      v_operand<=0;v_partial<=0;out_valid<=0;
      last_operand<=0;last_partial<=0;out_last<=0;
    end else begin
      v_operand<=in_valid;last_operand<=in_valid && in_last;
      if(in_valid)begin x_operand<=in_x;w_operand<=in_w;end
      v_partial<=v_operand;last_partial<=v_operand && last_operand;
      if(v_operand)begin
        partial_low<=x_operand*w_low;
        partial_high<=x_operand*w_high;
      end
      out_valid<=v_partial;out_last<=v_partial && last_partial;
      if(v_partial)out_product<=low_extended+high_shifted;
    end
  end
endmodule

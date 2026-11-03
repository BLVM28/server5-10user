// SPDX-License-Identifier: MIT
// The aligned operands overlap in product bits 8..31. Resolve bits 8..19
// first, register their carry with the upper operands, then resolve 20..31.
// Four registered stages, one product per cycle at steady state.
module kwt_mul16_pipe (
  input wire clk, rst_n, clear, in_valid, in_last,
  input wire signed [15:0] in_x, in_w,
  output reg out_valid, out_last,
  output reg signed [31:0] out_product
);
  reg v_operand, v_partial, v_join, last_operand, last_partial, last_join;
  reg signed [15:0] x_operand, w_operand;
  reg signed [24:0] partial_low;
  reg signed [23:0] partial_high;
  wire signed [8:0] w_low = $signed({1'b0,w_operand[7:0]});
  wire signed [7:0] w_high = $signed(w_operand[15:8]);
  wire signed [31:0] low_extended = {{7{partial_low[24]}},partial_low};
  wire signed [31:0] high_shifted = {partial_high,8'b0};
  wire [12:0] lower = {1'b0,low_extended[19:8]} + {1'b0,high_shifted[19:8]};
  reg [19:0] joined_low;
  reg [11:0] upper_low, upper_high;
  reg carry20;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      v_operand<=0;v_partial<=0;v_join<=0;out_valid<=0;
      last_operand<=0;last_partial<=0;last_join<=0;out_last<=0;
      x_operand<=0;w_operand<=0;partial_low<=0;partial_high<=0;out_product<=0;
    end
    else if(clear) begin
      v_operand<=0;v_partial<=0;v_join<=0;out_valid<=0;
      last_operand<=0;last_partial<=0;last_join<=0;out_last<=0;
    end else begin
      v_operand<=in_valid;last_operand<=in_valid && in_last;
      if(in_valid)begin x_operand<=in_x;w_operand<=in_w;end
      v_partial<=v_operand;last_partial<=v_operand && last_operand;
      if(v_operand)begin
        partial_low<=x_operand*w_low;
        partial_high<=x_operand*w_high;
      end
      v_join<=v_partial;last_join<=v_partial && last_partial;
      out_valid<=v_join;out_last<=v_join && last_join;
      if(v_join)out_product<={upper_low+upper_high+{11'd0,carry20},joined_low};
    end
  end
  // Valid bits flush these data registers on reset/clear; no consumer sees them
  // until a new valid partial product has written all four fields.
  always @(posedge clk) begin
    if(v_partial) begin
      joined_low<={lower[11:0],partial_low[7:0]};
      carry20<=lower[12];
      upper_low<=low_extended[31:20];
      upper_high<=high_shifted[31:20];
    end
  end
endmodule

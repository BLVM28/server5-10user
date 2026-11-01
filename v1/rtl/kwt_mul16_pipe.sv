// SPDX-License-Identifier: MIT
module kwt_mul16_pipe (
  input wire clk, rst_n, in_valid, in_last,
  input wire signed [15:0] in_x, in_w,
  output reg out_valid, out_last,
  output reg signed [31:0] out_product
);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin out_valid <= 0; out_last <= 0; out_product <= 0; end
    else begin
      out_valid <= in_valid;
      out_last <= in_valid && in_last;
      if (in_valid) out_product <= in_x * in_w;
    end
  end
endmodule

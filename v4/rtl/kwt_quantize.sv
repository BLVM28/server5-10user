// SPDX-License-Identifier: MIT
// F27 signed accumulator -> F11 int16, round to nearest, ties to even.
module kwt_quantize (
  input wire signed [39:0] acc,
  output reg signed [15:0] y,
  output reg saturated
);
  reg signed [39:0] q, rounded;
  reg increment;
  always @* begin
    q = acc >>> 16;
    increment = (acc[15:0] > 16'h8000) ||
                ((acc[15:0] == 16'h8000) && q[0]);
    rounded = q + (increment ? 40'sd1 : 40'sd0);
    saturated = 1'b0;
    if (rounded > 40'sd32767) begin y = 16'sh7fff; saturated = 1'b1; end
    else if (rounded < -40'sd32768) begin y = 16'sh8000; saturated = 1'b1; end
    else y = rounded[15:0];
  end
endmodule

// SPDX-License-Identifier: MIT
// Atomic fork/join: all lanes accept the same k together.
module kwt_mac8 (
  input wire clk, rst_n, clear,
  input wire cmd_valid, output wire cmd_ready,
  input wire [255:0] biases,
  input wire pair_valid, output wire pair_ready,
  input wire signed [15:0] x,
  input wire [127:0] weights,
  output wire out_valid, input wire out_ready,
  output wire [127:0] results,
  output wire [319:0] accumulators,
  output wire [7:0] saturated
);
  wire [7:0] cr, pr, ov;
  assign cmd_ready = &cr;
  assign pair_ready = &pr;
  assign out_valid = &ov;
  genvar i;
  generate for(i=0;i<8;i=i+1) begin: lane
    kwt_dot64 dot(.clk(clk),.rst_n(rst_n),.clear(clear),
      .cmd_valid(cmd_valid && cmd_ready),.cmd_ready(cr[i]),
      .cmd_bias(biases[32*i+:32]),
      .pair_valid(pair_valid && pair_ready),.pair_ready(pr[i]),
      .pair_x(x),.pair_w(weights[16*i+:16]),
      .out_valid(ov[i]),.out_ready(out_ready && out_valid),
      .out_y(results[16*i+:16]),.out_acc(accumulators[40*i+:40]),
      .out_saturated(saturated[i]),.busy());
  end endgenerate
endmodule

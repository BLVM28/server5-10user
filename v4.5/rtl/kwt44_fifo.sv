// SPDX-License-Identifier: MIT
// Power-of-two register FIFO. Ready and valid depend only on state.
module kwt44_fifo #(
  parameter integer WIDTH = 32,
  parameter integer DEPTH = 4,
  localparam integer PTR = $clog2(DEPTH)
) (
  input wire clk, rst_n,
  input wire push_valid,
  output wire push_ready,
  input wire [WIDTH-1:0] push_data,
  output wire pop_valid,
  input wire pop_ready,
  output wire [WIDTH-1:0] pop_data
);
  localparam [PTR:0] CAPACITY = {1'b1, {PTR{1'b0}}};
  reg [WIDTH-1:0] entries [0:DEPTH-1];
  reg [PTR-1:0] head, tail;
  reg [PTR:0] count;
  assign push_ready = rst_n && count != CAPACITY;
  assign pop_valid = rst_n && count != 0;
  assign pop_data = entries[head];
  wire push = push_valid && push_ready;
  wire pop = pop_valid && pop_ready;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      head <= 0;
      tail <= 0;
      count <= 0;
    end else begin
      if (push) tail <= tail + 1'b1;
      if (pop) head <= head + 1'b1;
      case ({push, pop})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: ;
      endcase
    end
  end
  always @(posedge clk)
    if (push) entries[tail] <= push_data;

  generate if (DEPTH < 2 || (DEPTH & (DEPTH-1)) != 0) begin: invalid_depth
    KWT44_FIFO_REQUIRES_POWER_OF_TWO invalid();
  end endgenerate
endmodule

// SPDX-License-Identifier: MIT
// Signed 16x16 with one accepted product per cycle. Register the two
// nibble products of each byte product before recombining them.
module kwt_mul16_pipe #(parameter ZERO_BUBBLES=0) (
  input wire clk, rst_n, clear, in_valid, in_last,
  input wire signed [15:0] in_x, in_w,
  output wire out_valid, out_last,
  output reg signed [31:0] out_product
);
  reg [6:0] valid_pipe, last_pipe;
  reg [7:0] x_byte[0:1], w_byte[0:1];
  wire [15:0] byte_product[0:3];
  genvar x_index, w_index;
  generate for(x_index=0;x_index<2;x_index=x_index+1)begin: x_part
    for(w_index=0;w_index<2;w_index=w_index+1)begin: w_part
      // The high byte of either operand is signed. Its low nibble
      // still contributes an unsigned digit.
      wire signed [4:0] x_lo=$signed({1'b0,x_byte[x_index][3:0]});
      wire signed [4:0] x_hi=$signed({x_index==1 && x_byte[x_index][7],x_byte[x_index][7:4]});
      wire signed [8:0] w_ext=$signed({w_index==1 && w_byte[w_index][7],w_byte[w_index]});
      reg signed [12:0] low_product,high_product;
      reg [6:0] low_sum;
      reg [5:0] high_sum;
      reg [3:0] byte_low;
      reg [15:0] combined;
      always @(posedge clk)begin
        low_product<=x_lo*w_ext;
        high_product<=x_hi*w_ext;
        low_sum<={1'b0,low_product[9:4]}+{1'b0,high_product[5:0]};
        high_sum<={{3{low_product[12]}},low_product[12:10]}+high_product[11:6];
        byte_low<=low_product[3:0];
        combined<={high_sum+{5'd0,low_sum[6]},low_sum[5:0],byte_low};
      end
      assign byte_product[2*x_index+w_index]=combined;
    end
  end endgenerate
  reg [31:0] base_product;
  reg signed [16:0] cross_product;
  wire cross_sign;
`ifdef KWT_USE_FOUNDRY_SRAM
`ifdef SYNTHESIS
  BUFV4_12TH40 cross_sign_driver(.I(cross_product[16]),.Z(cross_sign));
`else
  assign cross_sign = cross_product[16];
`endif
`else
  assign cross_sign = cross_product[16];
`endif
  wire [31:0] shifted_cross = {{8{cross_sign}}, cross_product[15:0], 8'b0};
  wire [12:0] lower_sum = {1'b0, base_product[19:8]} + {1'b0, shifted_cross[19:8]};
  reg [11:0] base_upper, cross_upper;
  reg [19:0] joined_lower;
  reg carry_to_upper;
  wire [12:0] upper_with_carry = {base_upper,1'b1} + {cross_upper,carry_to_upper};

  wire result_valid = !clear && valid_pipe[5];
  wire [31:0] result = {upper_with_carry[12:1], joined_lower};
  assign out_valid = valid_pipe[6];
  assign out_last = out_valid && last_pipe[6];
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) valid_pipe <= 0;
    else valid_pipe <= clear ? 7'd0 : {valid_pipe[5:0], in_valid};
  end
  generate if (ZERO_BUBBLES) begin: zero_bubbles
    // The asynchronous reset clears validity. A synchronous zero on an
    // invalid cycle keeps reset away from the wide accumulator data path.
    always @(posedge clk) out_product <= result_valid ? result : 32'd0;
  end else begin: hold_bubbles
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) out_product <= 0;
      else if (result_valid) out_product <= result;
    end
  end endgenerate

  always @(posedge clk) begin
    last_pipe <= {last_pipe[5:0], in_last};
    x_byte[0] <= in_x[7:0];
    x_byte[1] <= in_x[15:8];
    w_byte[0] <= in_w[7:0];
    w_byte[1] <= in_w[15:8];
    base_product <= {byte_product[3],byte_product[0]};
    cross_product <= $signed({byte_product[2][15],byte_product[2]})
                   + $signed({byte_product[1][15],byte_product[1]});
    base_upper <= base_product[31:20];
    cross_upper <= shifted_cross[31:20];
    joined_lower <= {lower_sum[11:0], base_product[7:0]};
    carry_to_upper <= lower_sum[12];
  end
endmodule

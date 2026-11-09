// SPDX-License-Identifier: MIT
// Result folding is a separate pipeline. The next dot may start immediately
// after the last product of this one, while its two outstanding carries close.
module kwt43_dot #(parameter ANNOUNCE=1)(
  input wire clk,rst_n,clear,valid,last,
  input wire signed [15:0] x,w,input wire signed [31:0] bias,
  output wire out_valid,output reg signed [15:0] y,output reg saturated
`ifndef SYNTHESIS
  ,output reg signed [39:0] acc
`endif
);
  wire product_valid,product_last;
  wire signed [31:0] product;
  kwt_mul16_pipe mul(.clk(clk),.rst_n(rst_n),.clear(clear),.in_valid(valid),.in_last(last),
    .in_x({x[15:1],1'b0}),.in_w({w[15:3],3'b000}),.out_valid(product_valid),.out_last(product_last),.out_product(product));
  reg first;
  reg [13:0] low_part;
  reg [12:0] middle_part,high_part;
  reg carry_low,carry_middle;
  wire [39:0] seed={{8{bias[31]}},bias},term={{8{product[31]}},product};
  wire [14:0] lo={1'b0,(first?seed[13:0]:low_part)}+{1'b0,term[13:0]};
  wire [13:0] mi={1'b0,(first?seed[26:14]:middle_part)}+{1'b0,term[26:14]}+{13'd0,!first&&carry_low};
  wire [12:0] hi=(first?seed[39:27]:high_part)+term[39:27]+{12'd0,!first&&carry_middle};
  reg finish1,finish2,finish3;
  reg [14:0] last_lo;
  reg [13:0] last_mi,fold_mi;
  reg [12:0] last_hi,fold_hi;
  reg [13:0] fold_lo;
  reg signed [39:0] canonical;
  wire signed [15:0] rounded;
  wire clipped;
  kwt_quantize quant(.acc(canonical),.y(rounded),.saturated(clipped));
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin first<=1;finish1<=0;finish2<=0;finish3<=0;end
    else if(clear)begin first<=1;finish1<=0;finish2<=0;finish3<=0;end
    else begin
      if(product_valid)first<=product_last;
      finish1<=product_valid && product_last;finish2<=finish1;finish3<=finish2;
    end
  end
  generate if(ANNOUNCE)begin: announce
    reg v;
    always @(posedge clk or negedge rst_n)
      if(!rst_n)v<=0;else if(clear)v<=0;else v<=finish3;
    assign out_valid=v;
  end else begin: silent
    assign out_valid=1'b0;
  end endgenerate
  always @(posedge clk)begin
    if(product_valid)begin
      low_part<=lo[13:0];middle_part<=mi[12:0];high_part<=hi;
      carry_low<=lo[14];carry_middle<=mi[13];
      if(product_last)begin last_lo<=lo;last_mi<=mi;last_hi<=hi;end
    end
    if(finish1)begin
      fold_lo<=last_lo[13:0];fold_mi<={1'b0,last_mi[12:0]}+last_lo[14];
      fold_hi<=last_hi+last_mi[13];
    end
    if(finish2)canonical<={fold_hi+{12'd0,fold_mi[13]},fold_mi[12:0],fold_lo};
    if(finish3)begin y<=rounded;saturated<=clipped;
`ifndef SYNTHESIS
      acc<=canonical;
`endif
    end
  end
endmodule

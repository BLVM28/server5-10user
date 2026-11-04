// SPDX-License-Identifier: MIT
// Eight independent row stripes. Four reconstructed values write four
// different stripes on the same edge. The padded row 99 is never stored.
module kwt43_xram(
  input wire clk,rst_n,wr_en,input wire [4:0] wr_block,input wire [5:0] wr_k,
  input wire [63:0] wr_data,input wire rd_en,input wire [3:0] rd_tile,input wire [5:0] rd_k,
  output reg rd_valid,output wire [127:0] rd_data
);
  genvar s;
  generate for(s=0;s<8;s=s+1)begin: stripe
    wire write_this=wr_en && wr_block[0]==(s/4) && !(wr_block==24 && s==3);
    wire [9:0] address=write_this ? {1'b0,wr_block[4:1],wr_k} : {rd_tile,rd_k};
    kwt_sp_ram #(.AW(10)) ram(.clk(clk),.en(write_this||rd_en),.we(write_this),
      .addr(address),.wdata(wr_data[16*(s%4)+:16]),.rdata(rd_data[16*s+:16]));
  end endgenerate
  always @(posedge clk or negedge rst_n)
    if(!rst_n)rd_valid<=0;else rd_valid<=rd_en;
endmodule

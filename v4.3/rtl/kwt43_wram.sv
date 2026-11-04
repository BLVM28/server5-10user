// SPDX-License-Identifier: MIT
// A page of sixteen columns. Every beat reconstructs columns 4*j+s.
module kwt43_wram(
  input wire clk,rst_n,wr_en,input wire [1:0] wr_quad,input wire [5:0] wr_k,
  input wire [63:0] wr_data,input wire rd_en,input wire [5:0] rd_k,
  output reg rd_valid,output wire [255:0] rd_data
);
  genvar l;
  generate for(l=0;l<16;l=l+1)begin: lane
    wire write_this=wr_en && wr_quad==l/4;
    kwt_sp_ram #(.AW(7)) ram(.clk(clk),.en(write_this||rd_en),.we(write_this),
      .addr({1'b0,write_this?wr_k:rd_k}),.wdata(wr_data[16*(l%4)+:16]),.rdata(rd_data[16*l+:16]));
  end endgenerate
  always @(posedge clk or negedge rst_n)
    if(!rst_n)rd_valid<=0;else rd_valid<=rd_en;
endmodule

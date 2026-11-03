// SPDX-License-Identifier: MIT
module kwt_w_panel #(parameter integer BANK_AW=7) (
  input wire clk,rst_n,
  input wire wr_en, wr_page, input wire [1:0] wr_pair,
  input wire [5:0] wr_k, input wire [31:0] wr_data,
  input wire rd_en, rd_page, input wire [5:0] rd_k,
  output reg rd_valid, output wire [127:0] rd_data
);
  genvar l;
  generate for(l=0;l<8;l=l+1) begin: lane
    wire sel=wr_en && wr_pair==(l/2);
    wire [6:0] word_addr = sel ? {wr_page,wr_k} : {rd_page,rd_k};
    wire [BANK_AW-1:0] a = {{(BANK_AW-7){1'b0}},word_addr};
    kwt_sp_ram #(.AW(BANK_AW)) ram(.clk(clk),.en(sel||rd_en),.we(sel),
      .addr(a),.wdata(wr_data[16*(l%2)+:16]),.rdata(rd_data[16*l+:16]));
  end endgenerate
  always @(posedge clk or negedge rst_n)
    if(!rst_n) rd_valid<=0; else rd_valid<=rd_en;
endmodule

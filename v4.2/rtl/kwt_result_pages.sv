// SPDX-License-Identifier: MIT
// The executor writes one row of eight results. DMA reads the opposite page.
module kwt_result_pages (
  input wire clk,wr_en,wr_page,input wire [6:0] wr_row,input wire [127:0] wr_data,
  input wire rd_en,rd_page,input wire [6:0] rd_row,output wire [127:0] rd_data
);
  reg selected;
  always @(posedge clk)if(rd_en)selected<=rd_page;
  wire [127:0] q[0:1];
  genvar p,l;
  generate for(p=0;p<2;p=p+1)begin: page
    wire wr=wr_en && wr_page==p;
    wire rd=rd_en && rd_page==p;
    for(l=0;l<8;l=l+1)begin: lane
      kwt_sp_ram #(.AW(7)) ram(.clk(clk),.en(wr||rd),.we(wr),.addr(wr?wr_row:rd_row),
        .wdata(wr_data[16*l+:16]),.rdata(q[p][16*l+:16]));
    end
  end endgenerate
  assign rd_data=q[selected];
endmodule

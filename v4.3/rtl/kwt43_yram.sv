// SPDX-License-Identifier: MIT
module kwt43_yram(
  input wire clk,wr_en,wr_page,input wire [6:0] wr_row,input wire [255:0] wr_data,
  input wire rd_en,rd_page,input wire [6:0] rd_row,output wire [255:0] rd_data
);
  reg selected;
  wire [255:0] q[0:1];
  always @(posedge clk)if(rd_en)selected<=rd_page;
  genvar p,l;
  generate for(p=0;p<2;p=p+1)begin: page
    wire write_this=wr_en && wr_page==p;
    wire read_this=rd_en && rd_page==p;
    for(l=0;l<16;l=l+1)begin: lane
      kwt_sp_ram #(.AW(7)) ram(.clk(clk),.en(write_this||read_this),.we(write_this),
        .addr(write_this?wr_row:rd_row),.wdata(wr_data[16*l+:16]),.rdata(q[p][16*l+:16]));
    end
  end endgenerate
  assign rd_data=q[selected];
endmodule

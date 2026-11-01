// SPDX-License-Identifier: MIT
module kwt_x_buffer (
  input wire clk,rst_n,
  input wire wr_en, input wire [12:0] wr_addr, input wire [15:0] wr_data,
  input wire rd_en, input wire [12:0] rd_addr,
  output reg rd_valid, output wire [15:0] rd_data
);
  wire [15:0] q[0:6];
  reg [2:0] rd_bank;
  genvar b;
  generate for(b=0;b<7;b=b+1) begin: bank
    wire select_write=wr_en && wr_addr[12:10]==b;
    wire select_read=rd_en && rd_addr[12:10]==b;
    kwt_sp_ram #(.AW(10)) ram(.clk(clk),.en(select_write||select_read),
      .we(select_write),.addr(select_write?wr_addr[9:0]:rd_addr[9:0]),
      .wdata(wr_data),.rdata(q[b]));
  end endgenerate
  assign rd_data=q[rd_bank];
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin rd_valid<=0; rd_bank<=0; end
    else begin rd_valid<=rd_en; if(rd_en) rd_bank<=rd_addr[12:10]; end
  end
endmodule

// SPDX-License-Identifier: MIT
// Rows 3*t+s reside in stripe s. Per stripe the first 32 rows use two
// 1024x16 macros; the last row uses a 128x16 macro. No dual-port inference.
module kwt_x_buffer (
  input wire clk,rst_n,wr_en,input wire [1:0] wr_stripe,
  input wire [5:0] wr_tile,input wire [4:0] wr_pair,input wire [31:0] wr_data,
  input wire rd_en,input wire [5:0] rd_tile,rd_k,
  output reg rd_valid,output wire [47:0] rd_data
);
  reg high_pending;
  reg [1:0] high_stripe;
  reg [5:0] high_tile;
  reg [4:0] high_pair;
  reg [15:0] high_data;
  wire write_access=wr_en || high_pending;
  wire [1:0] stripe=high_pending ? high_stripe : wr_stripe;
  wire [5:0] tile=high_pending ? high_tile : wr_tile;
  wire [4:0] pair_index=high_pending ? high_pair : wr_pair;
  wire [15:0] data_in=high_pending ? high_data : wr_data[15:0];
  reg [1:0] read_slice;
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin high_pending<=0;rd_valid<=0;end
    else begin high_pending<=wr_en;rd_valid<=rd_en;end
  end
  always @(posedge clk) begin
    if(wr_en) begin high_data<=wr_data[31:16];high_stripe<=wr_stripe;high_tile<=wr_tile;high_pair<=wr_pair;end
    if(rd_en)read_slice<=rd_tile[5:4];
  end
  genvar s,b;
  generate for(s=0;s<3;s=s+1)begin: stripe_ram
    wire [15:0] q[0:2];
    for(b=0;b<3;b=b+1)begin: slice
      localparam AW=(b==2)?7:10;
      wire wr=write_access && stripe==s && tile[5:4]==b;
      wire rd=rd_en && rd_tile[5:4]==b;
      wire [9:0] address=wr ? {tile[3:0],pair_index,high_pending} : {rd_tile[3:0],rd_k};
      kwt_sp_ram #(.AW(AW)) ram(.clk(clk),.en(wr||rd),.we(wr),.addr(address[AW-1:0]),.wdata(data_in),.rdata(q[b]));
    end
    assign rd_data[s*16+:16]=q[read_slice];
  end endgenerate
endmodule

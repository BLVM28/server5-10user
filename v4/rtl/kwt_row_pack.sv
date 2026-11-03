// SPDX-License-Identifier: MIT
// An exact transport codec AFTER the original rounding and saturation.
module kwt_row_pack (
  input wire clk,capture,compact,input wire [127:0] current,previous,
  output reg [1:0] mode,output reg [127:0] payload
);
  reg [127:0] absolute;
  wire [31:0] packed4;wire [63:0] packed8;wire [95:0] packed12;
  wire [7:0] fit4,fit8,fit12;
  genvar l;
  generate for(l=0;l<8;l=l+1)begin: lane
    wire signed [15:0] now=current[16*l+:16],prev=previous[16*l+:16];
    reg signed [16:0] delta;
    always @(posedge clk) if(capture)delta<=$signed({now[15],now})-$signed({prev[15],prev});
    assign fit4[l]=delta[16:3]=={14{delta[3]}};
    assign fit8[l]=delta[16:7]=={10{delta[7]}};
    assign fit12[l]=delta[16:11]=={6{delta[11]}};
    assign packed4[4*l+:4]=delta[3:0];
    assign packed8[8*l+:8]=delta[7:0];
    assign packed12[12*l+:12]=delta[11:0];
  end endgenerate
  always @(posedge clk)if(capture)absolute<=current;
  always @* begin
    if(compact && (&fit4))begin mode=0;payload={96'd0,packed4};end
    else if(compact && (&fit8))begin mode=1;payload={64'd0,packed8};end
    else if(compact && (&fit12))begin mode=2;payload={32'd0,packed12};end
    else begin mode=3;payload=absolute;end
  end
endmodule

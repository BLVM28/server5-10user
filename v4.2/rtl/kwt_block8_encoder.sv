// SPDX-License-Identifier: MIT
// Four pipeline stages from the eight completed int16 outputs to a 64-bit
// mantissa word and its shared exponent. No wide subtract in the shift path.
module kwt_block8_encoder(
  input wire clk,rst_n,valid, input wire [127:0] values,
  output reg out_valid,output reg [63:0] bytes,output reg [3:0] exponent
);
  reg v1,v2,v3;
  reg [127:0] a1,a2;
  reg [7:0] mask1;
  reg [3:0] e2,e3;
  wire [7:0] flags[0:7];
  wire [7:0] mask=flags[0]|flags[1]|flags[2]|flags[3]|flags[4]|flags[5]|flags[6]|flags[7];
  function automatic [3:0] shift_for(input [7:0] bits);
    casez(bits)
      8'b1???????:shift_for=8; 8'b01??????:shift_for=7;
      8'b001?????:shift_for=6; 8'b0001????:shift_for=5;
      8'b00001???:shift_for=4; 8'b000001??:shift_for=3;
      8'b0000001?:shift_for=2; 8'b00000001:shift_for=1;
      default:shift_for=0;
    endcase
  endfunction
  genvar l;
  generate for(l=0;l<8;l=l+1)begin: lane
    wire [15:0] x=values[l*16+:16];
    assign flags[l]=x[14:7]^{8{x[15]}};
    wire signed [16:0] twice=$signed({a2[l*16+:16],1'b0});
    wire signed [16:0] shifted=twice >>> e2;
    reg [8:0] rounded_input;
    always @(posedge clk) begin
      if(v2)rounded_input<=shifted[8:0];
      if(v3)bytes[l*8+:8]<=rounded_input[8:1]==8'd127 ? 8'd127 :
                              rounded_input[8:1]+{7'd0,rounded_input[0]};
    end
  end endgenerate
  always @(posedge clk or negedge rst_n)
    if(!rst_n)begin v1<=0;v2<=0;v3<=0;out_valid<=0;end
    else begin v1<=valid;v2<=v1;v3<=v2;out_valid<=v3;end
  always @(posedge clk)begin
    if(valid)begin a1<=values;mask1<=mask;end
    if(v1)begin a2<=a1;e2<=shift_for(mask1);end
    if(v2)e3<=e2;
    if(v3)exponent<=e3;
  end
endmodule

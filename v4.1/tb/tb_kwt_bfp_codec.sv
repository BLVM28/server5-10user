// Sweep every signed16 source, varying independent neighbouring lanes.
`timescale 1ns/1ps
module tb_kwt_bfp_codec;
  reg clk=0,rst_n=0,valid=0;
  reg [127:0] values;
  wire out_valid;wire [63:0] bytes;wire [3:0] exponent;
  reg [67:0] expected[0:65535];integer checked=0;
  kwt_block8_encoder dut(.*);always #5 clk=~clk;
  always @(negedge clk) if(out_valid)begin
    if({exponent,bytes}!==expected[checked])$fatal(1,"encoder at %0d",checked);
    checked=checked+1;
  end
  integer i,l,level,d,g,v,m,e,q;
  initial begin
    repeat(3)@(negedge clk);#1;rst_n=1;
    for(i=0;i<65536;i=i+1)begin
      @(negedge clk);#1;valid=1;level=0;
      for(l=0;l<8;l=l+1)begin
        v=i-32768;
        if(l>0) v=(i%5==0)? -(v/2) : v/(l+1);
        values[16*l+:16]=v;
        m=(v<0)?-1-v:v;
        if(m>level)level=m;
      end
      e=0;while((level>>e)>127)e=e+1;
      expected[i][67:64]=e;
      for(l=0;l<8;l=l+1)begin
        d=$signed(values[16*l+:16]);g=(1<<e);
        q=(d+(g/2))>>>e;if(q>127)q=127;
        expected[i][8*l+:8]=q;
      end
    end
    @(negedge clk);#1;valid=0;
    repeat(8)@(negedge clk);if(checked!=65536)$fatal(1,"encoder count %d",checked);
    $display("ALL PASS, 65536/65536 block8 encoder");$finish;
  end
endmodule

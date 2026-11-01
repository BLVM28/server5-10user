`timescale 1ns/1ps
// Directed 150 MHz pin-level check using the real default SRAM timing model.
// Stimulus changes on falling edges; this is not an ASIC path-delay signoff.
module tb_sram_150;
  reg clk=0;always #3.333334 clk=~clk;
  reg c128=1,c1024=1,gwen=1;
  reg [15:0] wen=16'hffff,data=0;
  reg [9:0] addr=0;
  wire [15:0] q128,q1024;
  reg [15:0] r128[0:127],r1024[0:1023];
  reg [15:0] mask,value,held128,held1024;
  integer i,j,checks=0;
  RAMSP128X16_rtl_top a(.CLK(clk),.CEN(c128),.GWEN(gwen),.WEN(wen),
    .A(addr[6:0]),.D(data),.Q(q128),.EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
  RAMSP1024X16_rtl_top b(.CLK(clk),.CEN(c1024),.GWEN(gwen),.WEN(wen),
    .A(addr),.D(data),.Q(q1024),.EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
  task access(input bit wr,input integer index,input [15:0] d,m,input bit small_enable);
    begin @(negedge clk);c1024=0;c128=!small_enable;gwen=!wr;
      addr=index;data=d;wen=m;@(posedge clk);#1.5;end
  endtask
  task compare(input bit small_enable);
    begin
      if(q1024!==r1024[addr])$fatal(1,"SP1024 mismatch address=%d",addr);
      checks=checks+1;
      if(small_enable)begin
        if(q128!==r128[addr[6:0]])$fatal(1,"SP128 mismatch address=%d",addr);
        checks=checks+1;
      end
    end
  endtask
  initial begin
    for(i=0;i<1024;i=i+1)begin
      value=16'ha59c^(i*16'h0173);r1024[i]=value;
      if(i<128)r128[i]=value;
      access(1,i,value,0,i<128);
    end
    for(i=0;i<1024;i=i+1)begin access(0,i,0,16'hffff,i<128);compare(i<128);end
    for(j=0;j<16;j=j+1)begin
      mask=~(16'h1<<j);value=~r1024[j];
      r1024[j]=(r1024[j]&mask)|(value&~mask);
      r128[j]=(r128[j]&mask)|(value&~mask);
      access(1,j,value,mask,1);access(0,j,0,16'hffff,1);compare(1);
    end
    held128=q128;held1024=q1024;
    @(negedge clk);c128=1;c1024=1;addr=900;data=16'hffff;gwen=0;wen=0;
    repeat(3)@(posedge clk);#1.5;
    if(q128!==held128||q1024!==held1024)$fatal(1,"Disabled SRAM changed Q");
    checks=checks+2;
    if(checks!=1186)$fatal(1,"Incomplete SRAM coverage");
    $display("ALL PASS, %0d/1186 SRAM checks at nominal 150 MHz",checks);$finish;
  end
  initial begin #100000;$fatal(1,"SRAM timeout");end
endmodule

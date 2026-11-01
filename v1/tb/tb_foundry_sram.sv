`timescale 1ns/1ps
module tb_foundry_sram;
  reg clk=0; always #5 clk=~clk;
  reg cen=1,gwen=1; reg [15:0] wen=16'hffff,d=0;
  reg [9:0] a=0;
  wire [15:0] q128,q1024;
  integer tests=0;
  RAMSP128X16_rtl_top r128(.CLK(clk),.CEN(cen),.GWEN(gwen),.WEN(wen),
    .A(a[6:0]),.D(d),.Q(q128),.EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
  RAMSP1024X16_rtl_top r1024(.CLK(clk),.CEN(cen),.GWEN(gwen),.WEN(wen),
    .A(a),.D(d),.Q(q1024),.EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
  task access(input bit write_access,input [9:0] address,input [15:0] data,mask);
    begin @(negedge clk); cen=0;gwen=!write_access;a=address;d=data;wen=mask;
      // Timing model default clock-to-Q is 1 ns; sample beyond that boundary.
      @(posedge clk); #2; end
  endtask
  task check(input [15:0] expected);
    begin if(q128!==expected || q1024!==expected)
      $fatal(1,"macro mismatch expected=%h sp128=%h sp1024=%h",expected,q128,q1024);
      tests=tests+1; end
  endtask
  initial begin
    access(1,0,16'h1357,16'h0000); access(0,0,0,16'hffff); check(16'h1357);
    access(1,0,16'h00a0,16'hff0f); access(0,0,0,16'hffff); check(16'h13a7);
    access(1,127,16'h8001,16'h0000); access(0,127,0,16'hffff); check(16'h8001);
    @(negedge clk);cen=1;a=0; @(posedge clk);#2; check(16'h8001);
    access(0,0,0,16'hffff); check(16'h13a7);
    access(1,1,16'hffff,16'h0000); access(1,2,16'h0000,16'h0000);
    access(0,1,0,16'hffff);check(16'hffff);access(0,2,0,16'hffff);check(0);
    $display("ALL PASS, %0d/7 real SP128/SP1024 macro checks",tests);$finish;
  end
  initial begin #10000;$fatal(1,"timeout");end
endmodule

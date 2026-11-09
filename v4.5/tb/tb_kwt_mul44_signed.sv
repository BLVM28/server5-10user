// SPDX-License-Identifier: MIT
`timescale 1ns/1ps
module tb_kwt_mul44_signed;
  reg clk=0, rst_n=0, clear=0, in_valid=0, in_last=0;
  reg signed [15:0] in_x=0, in_w=0;
  wire out_valid,out_last;
  wire signed [31:0] out_product;
  kwt_mul16_pipe dut(.*);
  always #3.333333 clk=~clk;

  reg signed [31:0] expected[0:16447];
  reg expected_last[0:16447];
  reg signed [15:0] edges[0:7];
  reg [31:0] random_state=32'h69cc6fb1;
  integer sent=0,seen=0;
  task automatic send(input signed [15:0] x,w,input bit last);
    @(negedge clk);
    in_valid=1;in_x=x;in_w=w;in_last=last;
    expected[sent]=x*w;
    expected_last[sent]=last;
    sent=sent+1;
  endtask
  always @(posedge clk) begin
    #0.001;
    if(rst_n && out_valid) begin
      if(seen>=sent || out_product!==expected[seen] || out_last!==expected_last[seen])
        $fatal(1,"SIGNED_MUL_MISMATCH index=%0d got=%h expected=%h last=%b/%b",seen,out_product,expected[seen],out_last,expected_last[seen]);
      seen=seen+1;
    end
  end
  initial begin
    edges[0]=16'sh8000; edges[1]=16'sh8001; edges[2]=-257; edges[3]=-1;
    edges[4]=0; edges[5]=1; edges[6]=255; edges[7]=16'sh7fff;
    repeat(3)@(negedge clk);
    rst_n=1;
    // Abort a partial sequence before its first result can retire.
    in_valid=1;in_x=-32768;in_w=-32768;
    repeat(2)@(negedge clk);
    clear=1;in_valid=0;
    @(negedge clk);clear=0;
    for(integer a=0;a<8;a=a+1)
      for(integer b=0;b<8;b=b+1)
        send(edges[a],edges[b],b==7);
    for(integer k=0;k<16384;k=k+1) begin
      if(k%29==0)begin @(negedge clk);in_valid=0;in_last=0;end
      random_state=1664525*random_state+1013904223;
      send(random_state[15:0],random_state[31:16],k%64==63);
    end
    @(negedge clk);in_valid=0;in_last=0;
    repeat(8)@(negedge clk);
    if(seen!=16448)$fatal(1,"SIGNED_MUL_COUNT %0d",seen);
    $display("ALL PASS, 16448/16448 signed products and last tags");
    $finish;
  end
endmodule

// Independent reference over the complete legal aligned operand range for the new uninterrupted accumulation path.
`timescale 1ns/1ps
module tb_kwt_stream_dot;
  reg clk=0,rst_n=0,clear=0,valid=0,last=0;
  reg signed [15:0] x=0,w=0;reg signed [31:0] bias=0;
  wire out_valid,saturated;wire signed [15:0] y;wire signed [39:0] acc;
  kwt43_dot dot(.*);
  always #5 clk=~clk;
  reg signed [63:0] expect_sum[0:63],sum,rounded;
  reg [31:0] random_state=32'h61f11235;
  integer sent=0,seen=0,m,k,b,clipped;
  always @(negedge clk)if(rst_n && out_valid)begin
    if(seen>=sent || acc!==expect_sum[seen][39:0])$fatal(1,"stream sum %d",seen);
    rounded=expect_sum[seen]>>>16;
    if(expect_sum[seen][15:0]>32768 || (expect_sum[seen][15:0]==32768 && rounded[0]))rounded=rounded+1;
    clipped=(rounded>32767 || rounded< -32768);
    if(rounded>32767)rounded=32767;
    if(rounded< -32768)rounded=-32768;
    if(y!==rounded[15:0] || saturated!==clipped[0])$fatal(1,"stream rounding %d",seen);
    seen=seen+1;
  end
  initial begin
    repeat(4)@(negedge clk);rst_n=1;
    valid=1;x=-32768;w=32767;repeat(31)@(negedge clk);
    clear=1;valid=0;@(negedge clk);clear=0;
    for(b=0;b<8;b=b+1)begin
      case(b%4)
        0:bias=32'sh7fffffff;1:bias=32'sh80000000;2:bias=32'sh00008000;3:bias=-32'sh00008000;
      endcase
      for(m=0;m<8;m=m+1)begin
        sum=bias;
        for(k=0;k<64;k=k+1)begin
          if(b[0] && k%11==3)begin valid=0;last=0;@(negedge clk);end
          valid=1;last=k==63;random_state=1664525*random_state+1013904223;
          case(m)
            0:begin x=-32768;w=-32768;end
            1:begin x=-32768;w=32767;end
            2:begin x=32767;w=(k%2)?-32768:32767;end
            3:begin x=0;w=32767;end
            default:begin x=random_state[15:0];w=random_state[31:16];end
          endcase
          x=x&16'hfffe;w=w&16'hfff8;
          sum=sum+$signed(x)*$signed(w);@(negedge clk);
        end
        expect_sum[sent]=sum;sent=sent+1;
      end
      valid=0;last=0;repeat(14)@(negedge clk);if(seen!=sent)$fatal(1,"stream missing result");
    end
    $display("ALL PASS, %0d/64 uninterrupted signed dots, abort, ties and saturation",seen);$finish;
  end
endmodule

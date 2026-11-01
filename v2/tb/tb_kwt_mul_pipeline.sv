`timescale 1ns/1ps
// Independent full-width multiply oracle, exhaustive w for eight x boundaries.
module tb_kwt_mul_pipeline;
  reg clk=0;always #5 clk=~clk;
  reg rst_n=0,clear=0,in_valid=0,in_last=0;
  reg signed [15:0] in_x=0,in_w=0;
  wire out_valid,out_last;wire signed [31:0] out_product;
  reg [2:0] valid_q=0,last_q=0;
  reg signed [31:0] products[0:2];
  reg signed [15:0] boundary[0:7];
  reg [31:0] rng=32'h20261101;
  integer checks=0,cycles=0,a,b,k;
  kwt_mul16_pipe dut(.*);
  always @(posedge clk) begin
    if(!rst_n||clear)begin valid_q=0;last_q=0;end
    else begin
      valid_q={valid_q[1:0],in_valid};last_q={last_q[1:0],in_valid&&in_last};
      products[2]=products[1];products[1]=products[0];
      products[0]=$signed(in_x)*$signed(in_w);
    end
    #1;
    if(out_valid!==valid_q[2]||out_last!==last_q[2])$fatal(1,"valid/last latency or reset mismatch");
    if(out_valid)begin
      if(out_product!==products[2])$fatal(1,"product mismatch got=%h expected=%h",out_product,products[2]);
      checks=checks+1;
    end
    cycles=cycles+1;
  end
  initial begin
    boundary[0]=-32768;boundary[1]=-32767;boundary[2]=-129;boundary[3]=-1;
    boundary[4]=0;boundary[5]=1;boundary[6]=255;boundary[7]=32767;
    repeat(4)@(negedge clk);rst_n=1;
    for(a=0;a<8;a=a+1)for(b=0;b<65536;b=b+1)begin
      @(negedge clk);in_valid=1;in_x=boundary[a];in_w=b[15:0];in_last=(b%64==63);
    end
    @(negedge clk);in_valid=0;repeat(4)@(negedge clk);
    if(checks!=524288)$fatal(1,"exhaustive count mismatch");
    // Bubbles and reset with each possible number of occupied pipeline stages.
    for(k=1;k<=3;k=k+1)begin
      repeat(k)begin @(negedge clk);in_valid=1;in_x=-32768;in_w=-1;in_last=1;end
      @(negedge clk);rst_n=0;in_valid=0;
      repeat(2)@(negedge clk);rst_n=1;repeat(4)@(negedge clk);
    end
    for(k=0;k<4096;k=k+1)begin
      @(negedge clk);rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
      in_valid=(k%5!=0);in_x=rng[15:0];in_w=rng[31:16];in_last=(k%19==0);
    end
    @(negedge clk);in_valid=0;repeat(5)@(negedge clk);
    for(k=1;k<=3;k=k+1)begin
      repeat(k)begin @(negedge clk);in_valid=1;in_x=-32768;in_w=-1;in_last=1;end
      @(negedge clk);clear=1;in_valid=0;
      @(negedge clk);clear=0;repeat(4)@(negedge clk);
    end
    $display("ALL PASS, 524288/524288 exhaustive products; total_checked=%0d with bubbles/resets",checks);$finish;
  end
  initial begin #10000000;$fatal(1,"pipeline test timeout");end
endmodule

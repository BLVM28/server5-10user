`timescale 1ns/1ps
module tb_raw_writer;
  reg clk=0,rst_n=0,start=0;
  reg [3:0] group_index=0,sy=0;
  wire done,mem_valid,ret_ready,y_read;
  wire [1:0] error;
  wire [31:0] addr,wdata;
  wire [6:0] y_addr;
  reg [255:0] y_vector;
  reg mem_ready=0,ret_valid=0;
  reg [63:0] keys=64'hfedcba9876543210;
  integer clocks=0,count=0,shift,value,expected,rounded,r,c,exhaustive=0;
  kwt43_writer dut(.clk(clk),.rst_n(rst_n),.start(start),.group_index(group_index),.sy(sy),.keys(keys),
    .yb(32'h10001000),.done(done),.error(error),.mem_valid(mem_valid),.addr(addr),.wdata(wdata),
    .mem_ready(mem_ready),.ret_valid(ret_valid),.ret_err(1'b0),.ret_ready(ret_ready),
    .y_read(y_read),.y_addr(y_addr),.y_vector(y_vector));
  always #5 clk=~clk;
  function automatic signed [15:0] sample(input integer row,col);
    sample=16'((row*1601+col*4111)^32'h8f04);
  endfunction
  function automatic [15:0] oracle(input integer val,scale);
    integer q;
    begin
      // Integer division truncates toward zero; explicitly implement floor.
      q=val+(1<<scale)/2;
      q=q<0?-((-q+(1<<scale)-1)/(1<<scale)):q/(1<<scale);
      if(q>32767/(1<<scale))q=32767/(1<<scale);
      if(q< -32768/(1<<scale))q= -32768/(1<<scale);
      oracle=16'(q*(1<<scale));
    end
  endfunction
  always @(posedge clk)begin
    clocks<=clocks+1;
    if(y_read)for(integer j=0;j<16;j=j+1)y_vector[16*j+:16]<=sample(y_addr,j);
    if(mem_valid&&mem_ready)begin
      if(!ret_ready)$fatal(1,"zero latency response not accepted");
      r=count/8;c=2*(count%8);
      if(addr!==32'h10001000+512*r+32*group_index+4*(count%8))$fatal(1,"address");
      if(wdata!=={oracle(int'(sample(r,c+1)),sy),oracle(int'(sample(r,c)),sy)})$fatal(1,"data");
      count=count+1;
    end
  end
  always @(negedge clk)begin
    mem_ready=(clocks%5!=0);
    ret_valid=mem_valid&&mem_ready;
  end
  initial begin
    for(shift=0;shift<6;shift=shift+1)for(value=-32768;value<=32767;value=value+1)begin
      if(dut.numeric_y(16'(value),4'(shift))!==oracle(value,shift))$fatal(1,"rounding %d %d",value,shift);
      exhaustive=exhaustive+1;
    end
    repeat(3)@(negedge clk);rst_n=1;
    for(shift=0;shift<6;shift=shift+1)begin
      @(negedge clk);sy=4'(shift);group_index=4'(shift*3);count=0;start=1;
      @(negedge clk);start=0;
      wait(done);@(negedge clk);
      if(error!=0||count!=792)$fatal(1,"completion");
      @(negedge clk);
    end
    $display("RAW_WRITER_PASS numeric_cases=%0d groups=6 words=4752",exhaustive);$finish;
  end
  initial begin #1000000;$fatal(1,"timeout");end
endmodule

`timescale 1ns/1ps
module tb_kwt_arithmetic;
  reg clk=0;always #5 clk=~clk;
  reg rst_n=0,cv=0,pv=0,orr=0;
  wire cr,pr,ov,busy,os;
  reg signed [31:0] bias=0;
  reg signed [15:0] x=0,w=0;
  wire signed [15:0] oy;wire signed [39:0] oa;
  reg signed [39:0] qa=0;wire signed [15:0] qy;wire qs;
  reg [39:0] q_acc[0:225],d_acc[0:31];
  reg [15:0] q_y[0:225],d_y[0:31],dx[0:2047],dw[0:2047];
  reg [3:0] q_sat[0:225],d_sat[0:31];reg [31:0] db[0:31];
  string dir;integer c,k,j,tests=0;
  kwt_quantize quant(.acc(qa),.y(qy),.saturated(qs));
  kwt_dot64 dut(.clk(clk),.rst_n(rst_n),.clear(1'b0),.cmd_valid(cv),.cmd_ready(cr),.cmd_bias(bias),
    .pair_valid(pv),.pair_ready(pr),.pair_x(x),.pair_w(w),.out_valid(ov),.out_ready(orr),
    .out_y(oy),.out_acc(oa),.out_saturated(os),.busy(busy));
  task reset_all;
    begin @(negedge clk);rst_n=0;cv=0;pv=0;orr=0;
      repeat(3) @(negedge clk);rst_n=1;@(negedge clk);
      if(!cr || ov || busy) $fatal(1,"reset protocol");end
  endtask
  task start(input integer idx);
    begin @(negedge clk);bias=db[idx];cv=1;
      @(posedge clk);if(!cr)$fatal(1,"not ready");
      @(negedge clk);cv=0;end
  endtask
  task pairs(input integer idx,input integer count);
    integer t;
    begin for(t=0;t<count;t=t+1) begin
      @(negedge clk);
      if(idx%2==1 && t%7==3) begin pv=0;@(negedge clk);end
      x=dx[idx*64+t];w=dw[idx*64+t];pv=1;cv=(t==20);
      @(posedge clk);if(!pr || cr)$fatal(1,"pair/busy handshake %d",t);
    end
    @(negedge clk);pv=0;cv=0;end
  endtask
  task check_result(input integer idx,input bit consume);
    integer t;
    begin wait(ov);@(negedge clk);
      for(t=0;t<5;t=t+1) begin
        if(!ov || oy!==d_y[idx] || oa!==d_acc[idx] || os!==d_sat[idx][0])
          $fatal(1,"dot case %0d y=%h/%h acc=%h/%h sat=%b/%b",idx,oy,d_y[idx],oa,d_acc[idx],os,d_sat[idx][0]);
        @(negedge clk);
      end
      if(consume) begin orr=1;@(negedge clk);orr=0;if(ov)$fatal(1,"response consumed twice");end
    end
  endtask
  initial begin
    if(!$value$plusargs("VEC_DIR=%s",dir))dir="../../vec";
    $readmemh({dir,"/quant_acc.hex"},q_acc);$readmemh({dir,"/quant_y.hex"},q_y);
    $readmemh({dir,"/quant_sat.hex"},q_sat);$readmemh({dir,"/dot_x.hex"},dx);
    $readmemh({dir,"/dot_w.hex"},dw);$readmemh({dir,"/dot_b.hex"},db);
    $readmemh({dir,"/dot_acc.hex"},d_acc);$readmemh({dir,"/dot_y.hex"},d_y);
    $readmemh({dir,"/dot_sat.hex"},d_sat);
    for(c=0;c<226;c=c+1) begin qa=q_acc[c];#1;
      if(qy!==q_y[c] || qs!==q_sat[c][0])$fatal(1,"quant case %0d",c);
      tests=tests+1;end
    reset_all();
    for(c=0;c<32;c=c+1)begin start(c);pairs(c,64);check_result(c,1);tests=tests+1;end
    start(3);pairs(3,13);reset_all();start(0);pairs(0,64);check_result(0,1);tests=tests+1;
    start(2);pairs(2,64);check_result(2,0);reset_all();start(5);pairs(5,64);check_result(5,1);tests=tests+1;
    $display("ALL PASS, %0d/260 arithmetic checks",tests);$finish;
  end
  initial begin #2000000;$fatal(1,"arithmetic timeout");end
endmodule

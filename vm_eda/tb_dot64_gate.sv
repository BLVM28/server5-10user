`timescale 1ns/1ps
// Observable-interface test for both RTL and a Genus-generated mapped netlist.
module tb_dot64_gate;
`ifndef KWT_PERIOD_NS
`define KWT_PERIOD_NS 6.666667
`endif
  reg clk=0;always #(`KWT_PERIOD_NS/2.0) clk=~clk;
  reg rst_n=0,cmd_valid=0,pair_valid=0,out_ready=0;
  wire clear=1'b0;
  wire cmd_ready,pair_ready,out_valid,busy;
  reg signed [31:0] cmd_bias=0;
  reg signed [15:0] pair_x=0,pair_w=0;
  wire signed [15:0] out_y;
  wire signed [39:0] out_acc;
  wire out_saturated;
  reg [15:0] xs[0:2047],ws[0:2047],ys[0:31];
  reg [31:0] biases[0:31];reg [39:0] accs[0:31];reg [3:0] sats[0:31];
  integer n,k,checks=0;string dir;
  kwt_dot64 dut(.*);
  // Drive at the explicit 1 ns external-input budget in constraints.tcl.
  task tick;
    begin @(posedge clk);#1.000;end
  endtask
  initial begin
`ifdef KWT_GATE_SIM
    // The runner copies and hashes the Tempus output into this working directory.
    $sdf_annotate("mapped.sdf",dut,,"sdf_annotation.log","MAXIMUM");
`endif
    if(!$value$plusargs("VEC_DIR=%s",dir))$fatal(1,"VEC_DIR is required");
    $readmemh({dir,"/dot_x.hex"},xs);$readmemh({dir,"/dot_w.hex"},ws);
    $readmemh({dir,"/dot_b.hex"},biases);$readmemh({dir,"/dot_y.hex"},ys);
    $readmemh({dir,"/dot_acc.hex"},accs);$readmemh({dir,"/dot_sat.hex"},sats);
    repeat(4)tick();rst_n=1;
    repeat(2)tick();
    for(n=0;n<32;n=n+1)begin
      while(!cmd_ready)tick();
      cmd_bias=biases[n];cmd_valid=1;tick();cmd_valid=0;
      for(k=0;k<64;k=k+1)begin
        if(k%7==3)begin pair_valid=0;tick();end
        while(!pair_ready)tick();
        pair_valid=1;pair_x=xs[n*64+k];pair_w=ws[n*64+k];tick();
      end
      pair_valid=0;
      while(!out_valid)tick();
      repeat(3)begin
        tick();
        if(out_y!==ys[n]||out_acc!==accs[n]||out_saturated!==sats[n][0])
          $fatal(1,"dot64 case=%d mismatch acc=%h expected=%h",n,out_acc,accs[n]);
      end
      out_ready=1;tick();out_ready=0;checks=checks+1;
    end
    $display("ALL PASS, %0d/32 dot64 vectors period_ns=%0.6f",checks,`KWT_PERIOD_NS);$finish;
  end
  initial begin #100000;$fatal(1,"dot64 timeout");end
endmodule

`timescale 1ns/1ps
module tb_v3_carries;
  reg clk=0, rst_n=0, clear=0, cmd_valid=0, pair_valid=0, out_ready=0;
  reg signed [31:0] cmd_bias;
  reg signed [15:0] pair_x, pair_w;
  wire cmd_ready, pair_ready, out_valid, out_saturated, busy;
  wire signed [39:0] out_acc;
  wire signed [15:0] out_y;
  longint signed reference_sum;
  integer tests=0;
  always #5 clk=~clk;
  kwt_dot64 dut(.*);

  task automatic issue(input integer pattern);
    integer k;
    begin
      @(negedge clk);
      case (pattern)
        0: cmd_bias=-1;                // both segment boundaries must ripple after last
        1: cmd_bias=32'h07ff_ffff;     // two pending carries on the same product
        2: cmd_bias=32'sh8000_0000;
        default: cmd_bias=32'sh7fff_ffff;
      endcase
      reference_sum=$signed(cmd_bias);
      cmd_valid=1;
      @(posedge clk); if (!cmd_ready) $fatal(1,"command not accepted");
      @(negedge clk); cmd_valid=0;
      for (k=0;k<64;k=k+1) begin
        if (k%9==4) begin pair_valid=0; @(negedge clk); end
        case (pattern)
          0: begin pair_x=1; pair_w=(k==63)?16'sd1:16'sd0; end
          1: begin pair_x=1; pair_w=(k==63)?16'sd16385:16'sd0; end
          2: begin pair_x=-16'sd32768; pair_w=-16'sd32768; end
          3: begin pair_x=-16'sd32768; pair_w=16'sd32767; end
          default: begin pair_x=(k*5387+901); pair_w=(k*2713-31768); end
        endcase
        pair_valid=1;
        reference_sum=reference_sum+$signed(pair_x)*$signed(pair_w);
        @(posedge clk); if (!pair_ready) $fatal(1,"pair %0d not accepted",k);
        @(negedge clk);
      end
      pair_valid=0;
    end
  endtask

  task automatic check_response;
    longint signed rounded;
    reg signed [15:0] expected_y;
    reg expected_sat;
    begin
      rounded=reference_sum >>> 16;
      if (reference_sum[15:0]>16'h8000 ||
          (reference_sum[15:0]==16'h8000 && rounded[0])) rounded=rounded+1;
      expected_sat=rounded>32767 || rounded< -32768;
      expected_y=rounded>32767 ? 16'h7fff : (rounded< -32768 ? 16'h8000 : rounded[15:0]);
      wait(out_valid);
      repeat(4) begin
        @(negedge clk);
        if (!out_valid || out_acc!==reference_sum[39:0] || out_y!==expected_y ||
            out_saturated!==expected_sat) $fatal(1,"response mismatch: %h / %h",out_acc,reference_sum);
      end
      out_ready=1; @(negedge clk); out_ready=0;
      if (out_valid || !cmd_ready) $fatal(1,"response not retired");
      tests=tests+1;
    end
  endtask

  task automatic abort_fold(input bit second_fold);
    begin
      issue(0);
      if (second_fold) wait(dut.state==dut.FOLD_LAST);
      else wait(dut.state==dut.FOLD_FIRST);
      @(negedge clk);
      if (second_fold) rst_n=0; else clear=1;
      @(negedge clk); rst_n=1; clear=0;
      repeat(4) begin @(negedge clk);
        if (out_valid || !cmd_ready) $fatal(1,"aborted result escaped");
      end
      issue(4); check_response();
    end
  endtask

  initial begin
    repeat(3) @(negedge clk); rst_n=1;
    for (integer n=0;n<5;n=n+1) begin issue(n); check_response(); end
    abort_fold(0); abort_fold(1);
    if (tests!=7) $fatal(1,"test count");
    $display("ALL PASS, 7/7 deferred carry / abort / recovery cases");
    $finish;
  end
  initial begin #200000; $fatal(1,"timeout"); end
endmodule

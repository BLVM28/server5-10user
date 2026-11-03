// Wave capture companion. The counting/scoreboard bench is identical to the measured top.
`timescale 1ns/1ps
module tb_kwt_precision_waves;
  tb_kwt_system #(.PRECISION(1)) bench();
  integer wave_ns;
  initial if($test$plusargs("WAVES"))begin
    if(!$value$plusargs("WAVE_NS=%d",wave_ns))wave_ns=200000;
    $dumpfile("waves.vcd");$dumpvars(2,bench.dut);
    #(wave_ns);$dumpoff;
  end
endmodule

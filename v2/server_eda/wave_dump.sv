// Optional VCD is portable between VCS and Verdi. Disabled for normal regression.
module kwt_wave_dump;
  integer wave_ns;
  initial if ($test$plusargs("WAVES")) begin
    if (!$value$plusargs("WAVE_NS=%d",wave_ns)) wave_ns=200000;
    $dumpfile("waves.vcd");
    $dumpvars(1, tb_kwt_system);
    #(wave_ns); $dumpoff;
  end
endmodule

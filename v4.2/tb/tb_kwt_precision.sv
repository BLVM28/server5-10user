`timescale 1ns/1ps
module tb_kwt_precision;
  tb_kwt_system #(.PRECISION(1),.EXPORT42(1)) bench();
endmodule

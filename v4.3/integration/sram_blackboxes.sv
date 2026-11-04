// SPDX-License-Identifier: MIT
// Structural-check stubs ONLY. Never include in a functional simulation.
// ASIC synthesis must link the real public Liberty cells with these names.
(* black_box="true" *) module RAMSP1024X16 (
  output [15:0] Q,input CLK,CEN,input [15:0] WEN,input [9:0] A,
  input [15:0] D,input [2:0] EMA,input [1:0] EMAW,input GWEN,RET1N
); endmodule
(* black_box="true" *) module RAMSP128X16 (
  output [15:0] Q,input CLK,CEN,input [15:0] WEN,input [6:0] A,
  input [15:0] D,input [2:0] EMA,input [1:0] EMAW,input GWEN,RET1N
); endmodule

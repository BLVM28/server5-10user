// SPDX-License-Identifier: MIT
// Public SRAM wrapper contract verified against server source. Functional read:
// address/control sampled at rising edge, Q available after that edge.
// No RAM reset. Validity is maintained by the caller.
module kwt_sp_ram #(parameter integer AW=10) (
  input wire clk, en, we,
  input wire [AW-1:0] addr,
  input wire [15:0] wdata,
  output wire [15:0] rdata
);
`ifdef KWT_USE_FOUNDRY_SRAM
  generate
    if(AW==10) begin: sp1024
`ifdef SYNTHESIS
      // Liberty cell is RAMSP1024X16; *_rtl_top is a simulation wrapper only.
      RAMSP1024X16 ram(.CLK(clk),.CEN(~en),.GWEN(~we),
`else
      RAMSP1024X16_rtl_top ram(.CLK(clk),.CEN(~en),.GWEN(~we),
`endif
        .WEN(we ? 16'h0000 : 16'hffff),.A(addr),.D(wdata),.Q(rdata),
        .EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
    end else if(AW==7) begin: sp128
`ifdef SYNTHESIS
      RAMSP128X16 ram(.CLK(clk),.CEN(~en),.GWEN(~we),
`else
      RAMSP128X16_rtl_top ram(.CLK(clk),.CEN(~en),.GWEN(~we),
`endif
        .WEN(we ? 16'h0000 : 16'hffff),.A(addr),.D(wdata),.Q(rdata),
        .EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
    end else begin: unsupported
      KWT_UNSUPPORTED_SRAM_DEPTH deliberate_elaboration_error();
    end
  endgenerate
`else
  // Simulation model is in tb/, deliberately absent from synthesis filelist.
  kwt_sram_sim #(.AW(AW)) sim(.clk(clk),.en(en),.we(we),
    .addr(addr),.wdata(wdata),.rdata(rdata));
`endif
endmodule

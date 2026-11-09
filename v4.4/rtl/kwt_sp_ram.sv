// SPDX-License-Identifier: MIT
// Capture the scheduled request on the preceding falling edge. The macro
// still samples on the rising edge and its array is never reset.
module kwt_sp_ram #(parameter integer AW=10) (
  input wire clk, rst_n, en, we,
  input wire [AW-1:0] addr,
  input wire [15:0] wdata,
  output wire [15:0] rdata
);
  reg request_enable, request_write;
  reg [AW-1:0] request_address;
  reg [15:0] request_data;
  always @(negedge clk or negedge rst_n) begin
    if (!rst_n) begin
      request_enable <= 1'b0;
      request_write <= 1'b0;
    end else begin
      request_enable <= en;
      request_write <= en && we;
    end
  end
  always @(negedge clk) begin
    if (en) request_address <= addr;
    if (en && we) request_data <= wdata;
  end
`ifdef KWT_USE_FOUNDRY_SRAM
  generate
    if(AW==10) begin: sp1024
`ifdef SYNTHESIS
      // Liberty cell is RAMSP1024X16; *_rtl_top is a simulation wrapper only.
      RAMSP1024X16 ram(.CLK(clk),.CEN(~request_enable),.GWEN(~request_write),
`else
      RAMSP1024X16_rtl_top ram(.CLK(clk),.CEN(~request_enable),.GWEN(~request_write),
`endif
        .WEN({16{~request_write}}),.A(request_address),.D(request_data),.Q(rdata),
        .EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
    end else if(AW==7) begin: sp128
`ifdef SYNTHESIS
      RAMSP128X16 ram(.CLK(clk),.CEN(~request_enable),.GWEN(~request_write),
`else
      RAMSP128X16_rtl_top ram(.CLK(clk),.CEN(~request_enable),.GWEN(~request_write),
`endif
        .WEN({16{~request_write}}),.A(request_address),.D(request_data),.Q(rdata),
        .EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
    end else begin: unsupported
      KWT_UNSUPPORTED_SRAM_DEPTH deliberate_elaboration_error();
    end
  endgenerate
`else
  // Simulation model is in tb/, deliberately absent from synthesis filelist.
  kwt_sram_sim #(.AW(AW)) sim(.clk(clk),.en(request_enable),.we(request_write),
    .addr(request_address),.wdata(request_data),.rdata(rdata));
`endif
endmodule

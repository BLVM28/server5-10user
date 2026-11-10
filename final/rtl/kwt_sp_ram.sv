// SPDX-License-Identifier: MIT
// Public SRAM wrapper contract verified against server source. Functional read:
// address/control sampled at rising edge, Q available after that edge.
// No RAM reset. Validity is maintained by the caller.
module kwt_sp_ram #(parameter integer AW=10) (
  input wire clk, rst_n, en, we,
  input wire [AW-1:0] addr,
  input wire [15:0] wdata,
  output wire [15:0] rdata
);
  reg en_q, we_q;
  reg [AW-1:0] addr_q;
  reg [15:0] wdata_q;

  // 锁存本次请求。SRAM 仍在原时钟的下一上升沿执行读写。
  always @(negedge clk or negedge rst_n) begin
    if (!rst_n) begin
      en_q <= 1'b0;
      we_q <= 1'b0;
    end else begin
      en_q <= en;
      // CEN qualifies the access. The read request must not feed the
      // write-enable D input through a redundant en gate.
      we_q <= we;
    end
  end
  always @(negedge clk) begin
    // en_q/we_q qualify the macro access and already clear on reset.
    // The address and write data are only consumed on a sampled request.
    addr_q <= addr;
    if (we) wdata_q <= wdata;
  end
`ifdef KWT_USE_FOUNDRY_SRAM
  wire [AW-1:0] macro_addr;
  wire [15:0] macro_wdata;
`ifdef SYNTHESIS
  // Match the drive requirement of the physical macro pins. These
  // buffers carry the sampled request without changing its phase.
  generate
    for(genvar bit_index=0;bit_index<AW;bit_index=bit_index+1)begin: drive_addr
      BUFV4_12TH40 driver(.I(addr_q[bit_index]),.Z(macro_addr[bit_index]));
    end
    for(genvar bit_index=0;bit_index<16;bit_index=bit_index+1)begin: drive_data
      if(AW==10)begin: x_bank
        BUFV16_12TH40 driver(.I(wdata_q[bit_index]),.Z(macro_wdata[bit_index]));
      end else begin: tile_bank
        BUFV4_12TH40 driver(.I(wdata_q[bit_index]),.Z(macro_wdata[bit_index]));
      end
    end
  endgenerate
`else
  assign macro_addr=addr_q;
  assign macro_wdata=wdata_q;
`endif
  generate
    if(AW==10) begin: sp1024
`ifdef SYNTHESIS
      // Liberty cell is RAMSP1024X16; *_rtl_top is a simulation wrapper only.
      RAMSP1024X16 ram(.CLK(clk),.CEN(~en_q),.GWEN(~we_q),
`else
      RAMSP1024X16_rtl_top ram(.CLK(clk),.CEN(~en_q),.GWEN(~we_q),
`endif
        .WEN(we_q ? 16'h0000 : 16'hffff),.A(macro_addr),.D(macro_wdata),.Q(rdata),
        .EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
    end else if(AW==7) begin: sp128
`ifdef SYNTHESIS
      RAMSP128X16 ram(.CLK(clk),.CEN(~en_q),.GWEN(~we_q),
`else
      RAMSP128X16_rtl_top ram(.CLK(clk),.CEN(~en_q),.GWEN(~we_q),
`endif
        .WEN(we_q ? 16'h0000 : 16'hffff),.A(macro_addr),.D(macro_wdata),.Q(rdata),
        .EMA(3'd2),.EMAW(2'd0),.RET1N(1'b1));
    end else begin: unsupported
      KWT_UNSUPPORTED_SRAM_DEPTH deliberate_elaboration_error();
    end
  endgenerate
`else
  // Simulation model is in tb/, deliberately absent from synthesis filelist.
  kwt_sram_sim #(.AW(AW)) sim(.clk(clk),.en(en_q),.we(we_q),
    .addr(addr_q),.wdata(wdata_q),.rdata(rdata));
`endif
endmodule

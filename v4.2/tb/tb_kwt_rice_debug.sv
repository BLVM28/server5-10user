// Diagnostic top for reproducing an unexpected stream rejection by layer/group.
`timescale 1ns/1ps
module tb_kwt_rice_debug;
  tb_kwt_system #(.PRECISION(1)) b();
  `define RD b.dut.core.dma.rice_in
  always @(posedge b.nice_clk)if(`RD.state==5 && ((`RD.consume && `RD.last) || (!`RD.consume && `RD.remaining==0 && !`RD.pending)))begin
    $display("RICE END t=%0t w=%0d g=%0d pair=%0d row=%0d odd=%0d wn=%0d k=%0d consume=%0d last=%0d tail=%0d rem=%0d pending=%0d valid=%0d count=%0d finish=%0d off=%0d cur=%h next=%h win=%h",
      $time,`RD.is_w,`RD.grp,`RD.pair,`RD.x_row,`RD.odd,`RD.w_number,`RD.key,`RD.consume,`RD.last,`RD.last_ok,`RD.remaining,`RD.pending,`RD.token_valid,`RD.unpack.count,`RD.unpack.finish,`RD.unpack.offset,`RD.unpack.current,`RD.unpack.following,`RD.unpack.window);
  end
  always @(posedge b.nice_clk)if(`RD.state==5&&`RD.remaining<=3)
    $display("TRACE rem=%0d addr=%h data=%h ack=%b issue=%b ready=%b count=%0d rd=%0d wr=%0d offset=%0d finish=%0d consume=%b pop=%b push=%b",
      `RD.remaining,`RD.addr,`RD.canon,`RD.ack,`RD.issuing,`RD.mem_ready,`RD.unpack.count,`RD.unpack.rd,`RD.unpack.wr,`RD.unpack.offset,`RD.unpack.finish,`RD.consume,`RD.unpack.pop,`RD.unpack.push);
  `undef RD
endmodule

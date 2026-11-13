// Explicit simulation surrogate; never evidence that the vendor model passed.
module kwt_sram_sim #(parameter integer AW=10) (
  input wire clk,en,we, input wire [AW-1:0] addr,
  input wire [15:0] wdata, output reg [15:0] rdata
);
  reg [15:0] mem [0:(1<<AW)-1];
  always @(posedge clk) if(en) begin
    if(we) mem[addr]<=wdata;
    else rdata<=mem[addr];
  end
endmodule

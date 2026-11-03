// SPDX-License-Identifier: MIT
// Three independent rows share one 8-column W read. Each MAC writes its own
// biased dot exactly once. FINISH is sticky until the scheduler starts a tile.
module kwt_tile_compute (
  input wire clk,rst_n,start,clear,input wire [255:0] biases,
  output wire rd_en,output reg [5:0] tile,k,input wire pair_valid,
  input wire [47:0] xs,input wire [127:0] weights,output wire pair_ready,
  output wire commit,output wire [6:0] row,output wire [127:0] y,
`ifndef SYNTHESIS
  output wire [319:0] acc,
`endif
  output wire [7:0] saturated,output wire done
);
  localparam IDLE=0,INIT=1,FEED=2,WAIT_MAC=3,SECOND=4,THIRD=5,FINISH=6;
  reg [2:0] state;
  reg [6:0] base_row;
  wire [2:0] ready,pr,valid;
  wire [127:0] ys[0:2];wire [319:0] sums[0:2];wire [7:0] sats[0:2];
  wire [1:0] stripe=state==SECOND ? 2'd1 : state==THIRD ? 2'd2 : 2'd0;
  assign commit=rst_n && !clear && ((state==WAIT_MAC && (&valid)) || state==SECOND || state==THIRD);
  assign row=base_row+{5'b0,stripe};
  assign y=ys[stripe];assign saturated=sats[stripe];
  // Waveform/scoreboard tap only. The production parent consumes Y and flags.
`ifndef SYNTHESIS
  assign acc=sums[stripe];
`endif
  assign pair_ready=&pr;assign rd_en=rst_n && !clear && state==FEED;
  assign done=state==FINISH;
  genvar s;
  generate for(s=0;s<3;s=s+1)begin: rows
    kwt_mac8 mac(.clk(clk),.rst_n(rst_n),.clear(clear),
      .cmd_valid(state==INIT && (&ready)),.cmd_ready(ready[s]),.biases(biases),
      .pair_valid(pair_valid && pair_ready),.pair_ready(pr[s]),.x(xs[16*s+:16]),.weights(weights),
      .out_valid(valid[s]),.out_ready(commit && stripe==s),.results(ys[s]),.accumulators(sums[s]),.saturated(sats[s]));
  end endgenerate
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin state<=IDLE;tile<=0;k<=0;base_row<=0;end
    else if(clear)state<=IDLE;
    else if(start)begin state<=INIT;tile<=0;base_row<=0;k<=0;end
    else case(state)
      INIT: if(&ready)begin k<=0;state<=FEED;end
      FEED: if(k==63)state<=WAIT_MAC;else k<=k+1'b1;
      WAIT_MAC: if(&valid)state<=SECOND;
      SECOND: state<=THIRD;
      THIRD: if(tile==32)state<=FINISH;
             else begin tile<=tile+1'b1;base_row<=base_row+7'd3;state<=INIT;end
      default: begin end
    endcase
  end
endmodule

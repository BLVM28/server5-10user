// SPDX-License-Identifier: MIT
// Issue k=0..63 continuously for successive groups of rows. The final group
// masks padded rows. The only visible outputs are the 99 real matrix rows.
module kwt_tile_compute #(parameter integer STRIPES=4)(
  input wire clk,rst_n,start,clear,input wire [255:0] biases,
  output wire rd_en,output reg [5:0] tile,k,input wire pair_valid,
  input wire [16*STRIPES-1:0] xs,input wire [127:0] weights,output wire pair_ready,
  output wire commit,output wire [6:0] row,output wire [127:0] y,
`ifndef SYNTHESIS
  output wire [319:0] acc,
`endif
  output wire [7:0] saturated,output reg done
);
  localparam FINAL_TILE=(99+STRIPES-1)/STRIPES-1;
  reg issuing,last_q;
  reg [1:0] tail;
  reg [6:0] head_row;
  wire [STRIPES*8-1:0] valid;
  wire [127:0] ys[0:STRIPES-1];wire [7:0] flags[0:STRIPES-1];
`ifndef SYNTHESIS
  wire [319:0] sums[0:STRIPES-1];
  assign acc=sums[tail];
`endif
  assign rd_en=rst_n && issuing && !clear;
  // The memory pipeline is always accepted. Clear cancels a returning operand.
  assign pair_ready=rst_n;
  assign commit=rst_n && !clear && (valid[0] || tail!=0);
  assign row=head_row+tail;assign y=ys[tail];assign saturated=flags[tail];
  genvar s,l;
  generate for(s=0;s<STRIPES;s=s+1)begin: rows
    for(l=0;l<8;l=l+1)begin: lane
      kwt_stream_dot dot(.clk(clk),.rst_n(rst_n),.clear(clear||start),.valid(pair_valid),.last(last_q),
        .x(xs[16*s+:16]),.w(weights[16*l+:16]),.bias(biases[32*l+:32]),
        .out_valid(valid[s*8+l]),.y(ys[s][16*l+:16]),.saturated(flags[s][l])
`ifndef SYNTHESIS
        ,.acc(sums[s][40*l+:40])
`endif
      );
    end
  end endgenerate
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin issuing<=0;tile<=0;k<=0;last_q<=0;done<=0;head_row<=0;tail<=0;end
    else if(clear||start)begin
      issuing<=start && !clear;tile<=0;k<=0;last_q<=0;done<=0;head_row<=0;tail<=0;
    end else begin
      last_q<=rd_en && k==63;
      if(rd_en)begin
        k<=k+1'b1;
        if(k==63)begin
          if(tile==FINAL_TILE)issuing<=0;
          else tile<=tile+1'b1;
        end
      end
      if(commit)begin
        if(row==98)begin done<=1;tail<=0;end
        else if(tail==STRIPES-1)begin head_row<=head_row+STRIPES;tail<=0;end
        else tail<=tail+1'b1;
      end
    end
  end
endmodule

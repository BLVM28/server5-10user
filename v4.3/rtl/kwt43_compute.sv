// SPDX-License-Identifier: MIT
// Eight rows by sixteen columns. Dot pipelines overlap adjacent k sequences.
module kwt43_compute(
  input wire clk,rst_n,start,clear,input wire [511:0] biases,
  output wire rd_en,output reg [3:0] tile,output reg [5:0] k,
  input wire pair_valid,input wire [127:0] xs,input wire [255:0] weights,
  output wire commit,output wire [6:0] row,output wire [255:0] y,
  output wire [15:0] saturated,output reg done
`ifndef SYNTHESIS
  ,output wire [639:0] acc
`endif
);
  reg issuing,last_q;
  reg [2:0] tail;
  reg [6:0] head_row;
  wire announced;
  wire [255:0] ys[0:7];wire [15:0] flags[0:7];
`ifndef SYNTHESIS
  wire [639:0] sums[0:7];
  assign acc=sums[tail];
`endif
  assign rd_en=rst_n && issuing && !clear;
  assign commit=rst_n && !clear && (announced || tail!=0);
  assign row=head_row+{4'd0,tail};
  assign y=ys[tail];assign saturated=flags[tail];
  genvar s,l;
  generate for(s=0;s<8;s=s+1)begin: rows
    for(l=0;l<16;l=l+1)begin: lane
      wire result_valid;
      kwt43_dot #(.ANNOUNCE(s==0&&l==0)) dot(.clk(clk),.rst_n(rst_n),.clear(clear||start),
        .valid(pair_valid),.last(last_q),.x(xs[16*s+:16]),.w(weights[16*l+:16]),
        .bias(biases[32*l+:32]),.out_valid(result_valid),.y(ys[s][16*l+:16]),.saturated(flags[s][l])
`ifndef SYNTHESIS
        ,.acc(sums[s][40*l+:40])
`endif
      );
      if(s==0&&l==0)assign announced=result_valid;
    end
  end endgenerate
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n)begin issuing<=0;tile<=0;k<=0;last_q<=0;done<=0;head_row<=0;tail<=0;end
    else if(clear||start)begin issuing<=start&&!clear;tile<=0;k<=0;last_q<=0;done<=0;head_row<=0;tail<=0;end
    else begin
      last_q<=rd_en && k==63;
      if(rd_en)begin
        k<=k+1'b1;
        if(k==63)begin
          if(tile==12)issuing<=0;else tile<=tile+1'b1;
        end
      end
      if(commit)begin
        if(row==98)begin done<=1;tail<=0;end
        else if(tail==7)begin head_row<=head_row+8;tail<=0;end
        else tail<=tail+1'b1;
      end
    end
  end
endmodule

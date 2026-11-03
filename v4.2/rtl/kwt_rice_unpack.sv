// SPDX-License-Identifier: MIT
// Four 32-bit input words, an LSB-first cursor, and a four-one escape.
// The cursor moves only on consume. Refilling and decoding may coincide.
module kwt_rice_unpack(
  input wire clk,rst_n,clear,push,input wire [31:0] word,input wire [3:0] key,shift,
  input wire consume,output wire room,valid,absolute,tail_clean,
  output wire signed [16:0] value
);
  reg [31:0] words[0:3];
  reg [1:0] rd,wr;
  reg [2:0] count;
  reg [4:0] offset;
  wire [1:0] next_rd=rd+1'b1;
  // Only a queued second word may affect the prefix or cursor width. If the
  // prefix crosses a single word, zero extension makes finish exceed 32 and
  // stalls without exposing uninitialized storage to the FIFO push/pop count.
  wire [31:0] current=words[rd],following=count>1 ? words[next_rd] : 32'd0;
  wire [63:0] joined={following,current};
  wire [19:0] window=joined>>offset;
  assign absolute=&window[3:0];
  wire [1:0] unary=!window[0]?0:!window[1]?1:!window[2]?2:3;
  wire [4:0] width=absolute ? 5'd20-{1'b0,shift} : {1'b0,key}+{3'b0,unary}+1'b1;
  wire [5:0] finish={1'b0,offset}+width;
  wire [15:0] mask=(16'd1<<key)-1'b1;
  wire [16:0] zz=({15'd0,unary}<<key) | ((window>>({1'b0,unary}+3'd1))&mask);
  wire signed [15:0] left=window[19:4]<<shift;
  wire signed [15:0] escaped=left>>>shift;
  assign value=absolute ? $signed({escaped[15],escaped}) : $signed(({1'b0,zz[16:1]})^{17{zz[0]}});
  assign valid=count>1 || (count==1 && finish<=32);
  assign room=count<4;
  wire pop=consume && finish>=32;
  wire [31:0] endword=finish>32 ? following : current;
  assign tail_clean=count==(finish>32?2:1) &&
                    (finish[4:0]==0 || (endword>>finish[4:0])==0);
  always @(posedge clk)if(push)words[wr]<=word;
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin rd<=0;wr<=0;count<=0;offset<=0;end
    else if(clear)begin rd<=0;wr<=0;count<=0;offset<=0;end
    else begin
      if(push)wr<=wr+1'b1;
      if(pop)rd<=next_rd;
      if(consume)offset<=finish[4:0];
      case({push,pop})
        2'b10:count<=count+1'b1;
        2'b01:count<=count-1'b1;
        default:begin end
      endcase
    end
  end
endmodule

// SPDX-License-Identifier: MIT
// Assemble variable-size tokens into 32-bit ICB beats. Unused final bits are zero.
module kwt_rice_pack(
  input wire clk,rst_n,clear,input wire token_valid,input wire [19:0] token,input wire [4:0] width,
  input wire flush,output wire room,empty,output wire word_valid,input wire pop,output wire [31:0] word
);
  reg [31:0] partial,queue[0:3];reg [4:0] used;
  reg [1:0] rd,wr;reg [2:0] count;
  wire [5:0] total={1'b0,used}+{1'b0,width};
  wire [63:0] joined={32'd0,partial}|({44'd0,token}<<used);
  wire push_token=token_valid && room;
  wire pad=flush && used!=0 && room;
  wire enq=(push_token && total>=32) || pad;
  assign room=count<4;assign word_valid=count!=0;assign word=queue[rd];
  assign empty=count==0 && used==0;
  always @(posedge clk)if(enq)queue[wr]<=pad?partial:joined[31:0];
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin partial<=0;used<=0;rd<=0;wr<=0;count<=0;end
    else if(clear)begin partial<=0;used<=0;rd<=0;wr<=0;count<=0;end
    else begin
      if(push_token)begin partial<=total>=32?joined[63:32]:joined[31:0];used<=total[4:0];end
      else if(pad)begin partial<=0;used<=0;end
      if(enq)wr<=wr+1'b1;
      if(pop)rd<=rd+1'b1;
      case({enq,pop})
        2'b10:count<=count+1'b1;
        2'b01:count<=count-1'b1;
        default:begin end
      endcase
    end
  end
endmodule

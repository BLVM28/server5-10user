// SPDX-License-Identifier: MIT
// The eight predictors use reconstructed quantized values. An escape emits
// the absolute code. Both inputs to the difference are 16-bit signed.
module kwt_rice_writer #(parameter integer PACK_LOW_FIRST=1)(
  input wire clk,rst_n,start,input wire [4:0] group_index,input wire [3:0] sy,
  input wire [31:0] wb,yb,output wire done,output reg [1:0] error,
  output wire mem_valid,mem_read,output wire [31:0] addr,wdata,input wire mem_ready,
  input wire ret_valid,ret_err,input wire [31:0] ret_data,output wire ret_ready,
  output wire y_read,output wire [6:0] y_addr,input wire [127:0] y_vector
);
  localparam IDLE=0,KEY_REQ=1,KEY_WAIT=2,HEADER_REQ=3,HEADER_WAIT=4,DATA=5,FINISH=6;
  localparam STOP=0,READ_FIRST=1,LATCH_ROW=2,SYMBOLS=3,ENDED=4;
  reg [2:0] state,producer;
  reg [3:0] scale;reg [31:0] meta_addr,out_addr,keys;
  reg [6:0] row;reg [2:0] lane;
  reg [127:0] current;
  reg pending;
  wire room,empty,word_valid;wire [31:0] word;
  assign mem_valid=rst_n && (state==KEY_REQ || state==HEADER_REQ || (state==DATA && !pending && word_valid));
  assign addr=state==KEY_REQ?meta_addr:out_addr;
  wire [31:0] canonical=state==HEADER_REQ?keys:word;
  assign wdata=PACK_LOW_FIRST?canonical:{canonical[15:0],canonical[31:16]};
  assign mem_read=state==KEY_REQ;
  assign ret_ready=rst_n && (state==KEY_WAIT||state==HEADER_WAIT||(state==DATA&&pending));
  assign done=state==FINISH;
  wire advance=room;
  wire issue=producer==SYMBOLS && advance;
  assign y_read=rst_n && (producer==READ_FIRST || (issue && lane==6 && row!=98));
  assign y_addr=(producer==READ_FIRST)?7'd0:row+1'b1;
  reg v1,v2,v3;
  reg [2:0] l1;
  reg first1;reg [3:0] k1,k2;
  reg signed [15:0] q1,q2;
  reg signed [15:0] previous[0:7];
  reg [16:0] zigzag2;
  reg [19:0] token3;reg [4:0] width3;
  wire signed [15:0] ys=$signed(current[16*lane+:16]);
  wire signed [16:0] twice=$signed({ys,1'b0})>>>scale;
  wire signed [15:0] base=$signed(twice[16:1]);
  wire signed [15:0] ceiling=$signed(16'h7fff)>>>scale;
  wire signed [15:0] rounded=(base==ceiling)?base:base+{15'd0,twice[0]};
  wire signed [15:0] old_q=first1?16'sd0:previous[l1];
  wire signed [16:0] difference=$signed({q1[15],q1})-$signed({old_q[15],old_q});
  wire [16:0] quotient=zigzag2>>k2;
  wire [15:0] remainder=zigzag2&((16'd1<<k2)-1'b1);
  wire [2:0] prefix_len={1'b0,quotient[1:0]}+1'b1;
  wire [19:0] short_code=({4'd0,remainder}<<prefix_len)|((20'd1<<quotient[1:0])-1'b1);
  wire [15:0] literal=q2&(16'hffff>>scale);
  wire clear_pipe=start || state==IDLE || state==FINISH;
  wire encoder_done=producer==ENDED&&!v1&&!v2&&!v3;
  wire pop=state==DATA && mem_valid && mem_ready;
  kwt_rice_pack packer(.clk(clk),.rst_n(rst_n),.clear(clear_pipe),.token_valid(v3),
    .token(token3),.width(width3),.flush(encoder_done),.room(room),.empty(empty),.word_valid(word_valid),.pop(pop),.word(word));
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin v1<=0;v2<=0;v3<=0;end
    else if(clear_pipe)begin v1<=0;v2<=0;v3<=0;end
    else if(advance)begin v1<=issue;v2<=v1;v3<=v2;end
  end
  always @(posedge clk)begin
    if(advance && issue)begin q1<=rounded;k1<=keys[4*lane+:4];l1<=lane;first1<=row==0;end
    if(advance && v1)begin
      previous[l1]<=q1;q2<=q1;k2<=k1;zigzag2<=(difference<<1)^{17{difference[16]}};
    end
    if(advance && v2)begin
      token3<=quotient>=4?{literal,4'hf}:short_code;
      width3<=quotient>=4?5'd20-{1'b0,scale}:{1'b0,k2}+prefix_len;
    end
    if(producer==LATCH_ROW || (issue && lane==7 && row!=98))current<=y_vector;
  end
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin producer<=STOP;row<=0;lane<=0;end
    else if(clear_pipe)begin producer<=STOP;row<=0;lane<=0;end
    else if(state==KEY_WAIT && ret_valid && !ret_err)producer<=READ_FIRST;
    else case(producer)
      READ_FIRST:producer<=LATCH_ROW;
      LATCH_ROW:producer<=SYMBOLS;
      SYMBOLS:if(issue)begin lane<=lane+1'b1;if(lane==7)begin
        if(row==98)producer<=ENDED;else row<=row+1'b1;
      end end
      default:begin end
    endcase
  end
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin state<=IDLE;error<=0;pending<=0;scale<=0;meta_addr<=0;out_addr<=0;keys<=0;end
    else case(state)
      IDLE:if(start)begin
        scale<=sy;error<=0;pending<=0;meta_addr<=wb+{16'd0,group_index,11'd8};out_addr<=yb+{16'd0,group_index,11'd0};state<=KEY_REQ;
      end
      KEY_REQ:if(mem_ready)state<=KEY_WAIT;
      KEY_WAIT:if(ret_valid)begin
        if(ret_err)begin error<=2;state<=FINISH;end
        else begin keys<=PACK_LOW_FIRST?ret_data:{ret_data[15:0],ret_data[31:16]};state<=HEADER_REQ;end
      end
      HEADER_REQ:if(mem_ready)state<=HEADER_WAIT;
      HEADER_WAIT:if(ret_valid)begin
        if(ret_err)begin error<=3;state<=FINISH;end
        else begin out_addr<=out_addr+4;state<=DATA;end
      end
      DATA:begin
        if(pop)begin pending<=1;out_addr<=out_addr+4;end
        if(pending&&ret_valid)begin pending<=0;if(ret_err)begin error<=3;state<=FINISH;end end
        if(encoder_done&&empty&&!pending)state<=FINISH;
      end
      FINISH:state<=IDLE;
      default:state<=IDLE;
    endcase
  end
endmodule

// SPDX-License-Identifier: MIT
// X is stored by feature pair then row (two predictors). W is k-major
// within an eight-column group. A count header bounds every physical read.
module kwt_rice_reader #(parameter integer PACK_LOW_FIRST=1,STRIPES=4)(
  input wire clk,rst_n,start,weights,input wire [4:0] group_index,input wire [3:0] sx,sw,
  input wire [31:0] xb,wb,bb,output wire done,output reg [1:0] error,
  output wire mem_valid,output reg [31:0] addr,input wire mem_ready,
  input wire ret_valid,ret_err,input wire [31:0] ret_data,output wire ret_ready,
  output wire x_write,w_write,b_write,output wire [1:0] x_stripe,output wire [5:0] x_tile,
  output wire [4:0] x_pair,output wire [7:0] w_index,output wire [2:0] b_index,output wire [31:0] pair_data
);
  localparam IDLE=0,HEAD_REQ=1,HEAD_WAIT=2,KEY_REQ=3,KEY_WAIT=4,STREAM=5,B_REQ=6,B_WAIT=7,DRAIN=8,FINISH=9;
  reg [3:0] state,scale;
  reg is_w,pending;
  reg [4:0] grp,pair;
  reg [2:0] key_word,bias_index;
  reg [11:0] remaining;
  reg [31:0] keys[0:7];
  reg [8:0] w_number;
  reg [6:0] x_row;
  reg [1:0] stripe;
  reg [5:0] tile;
  reg odd;
  wire [31:0] canon=PACK_LOW_FIRST?ret_data:{ret_data[15:0],ret_data[31:16]};
  wire fifo_room,token_valid,literal,last_ok;
  wire signed [16:0] token;
  wire [31:0] key_group=keys[is_w?3'd0:pair[4:2]];
  wire [2:0] key_lane=is_w?w_number[2:0]:{pair[1:0],odd};
  wire [3:0] key=key_group[4*key_lane+:4];
  wire last=is_w ? w_number==511 : pair==31 && x_row==98 && odd;
  wire consume=state==STREAM && token_valid && !(pending&&ret_valid&&ret_err);
  wire issuing=state==STREAM && !pending && remaining!=0 && fifo_room;
  assign mem_valid=rst_n && (issuing||state==HEAD_REQ||state==KEY_REQ||state==B_REQ);
  assign ret_ready=rst_n && (state==HEAD_WAIT||state==KEY_WAIT||state==B_WAIT||((state==STREAM||state==DRAIN)&&pending));
  wire ack=ret_valid&&ret_ready;
  kwt_rice_unpack unpack(.clk(clk),.rst_n(rst_n),.clear(state!=STREAM),.push(state==STREAM&&ack&&!ret_err),.word(canon),
    .key(key),.shift(scale),.consume(consume),.room(fifo_room),.valid(token_valid),.absolute(literal),.tail_clean(last_ok),.value(token));
  // Token expansion is registered off the bit-cursor path. In X order the
  // next use of a predictor is two tokens later. Complete pairs write once.
  reg emit,emit_odd,base_zero;
  reg [1:0] saved_stripe;reg [5:0] saved_tile;reg [4:0] saved_pair;reg [7:0] saved_index;
  reg signed [16:0] saved_value;
  reg signed [15:0] prev0,prev1;reg [15:0] first_half;
  wire signed [15:0] prev=emit_odd?prev1:prev0;
  wire [15:0] code=saved_value+(base_zero?16'd0:prev);
  wire [15:0] expanded=code<<scale;
  assign pair_data={expanded,first_half};
  assign x_write=rst_n && emit && emit_odd && !is_w;assign w_write=rst_n && emit && emit_odd && is_w;
  assign x_stripe=saved_stripe;assign x_tile=saved_tile;assign x_pair=saved_pair;assign w_index=saved_index;
  assign b_write=state==B_WAIT && ack && !ret_err;assign b_index=bias_index;assign done=state==FINISH;
  always @(posedge clk or negedge rst_n)if(!rst_n)emit<=0;else emit<=consume;
  always @(posedge clk)begin
    if(consume)begin
      saved_value<=token;emit_odd<=is_w?w_number[0]:odd;base_zero<=literal||is_w||x_row==0;
      saved_index<=w_number[8:1];saved_stripe<=stripe;saved_tile<=tile;saved_pair<=pair;
    end
    if(emit)begin
      if(emit_odd)prev1<=code;else begin prev0<=code;first_half<=expanded;end
    end
    if(state==KEY_WAIT&&ack&&!ret_err)keys[key_word]<=canon;
  end
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin state<=IDLE;error<=0;addr<=0;is_w<=0;pending<=0;remaining<=0;key_word<=0;
      scale<=0;grp<=0;pair<=0;w_number<=0;x_row<=0;odd<=0;stripe<=0;tile<=0;bias_index<=0;end
    else case(state)
      IDLE:if(start)begin
        is_w<=weights;grp<=group_index;scale<=weights?sw:sx;
        addr<=weights ? wb+{16'd0,group_index,11'd0} : xb;
        error<=0;pending<=0;key_word<=0;pair<=0;w_number<=0;x_row<=0;odd<=0;stripe<=0;tile<=0;bias_index<=0;
        state<=HEAD_REQ;
      end
      HEAD_REQ:if(mem_ready)state<=HEAD_WAIT;
      HEAD_WAIT:if(ack)begin
        if(ret_err || canon==0 || canon>(is_w?320:3960))begin error<=ret_err?2:1;state<=DRAIN;end
        else begin remaining<=canon[11:0];addr<=addr+4;state<=KEY_REQ;end
      end
      KEY_REQ:if(mem_ready)state<=KEY_WAIT;
      KEY_WAIT:if(ack)begin
        if(ret_err)begin error<=2;state<=DRAIN;end
        else begin addr<=addr+(is_w?8:4);
          if(is_w||key_word==7)state<=STREAM;
          else begin key_word<=key_word+1'b1;state<=KEY_REQ;end
        end
      end
      STREAM:begin
        if(issuing&&mem_ready)begin pending<=1;remaining<=remaining-1'b1;addr<=addr+4;end
        if(ack)pending<=0;
        if(ack&&ret_err)begin error<=2;state<=DRAIN;end
        else if(consume)begin
          if(last)begin
            if(!last_ok || remaining!=0 || pending)begin error<=1;state<=DRAIN;end
            else if(is_w)begin addr<=bb+{22'd0,grp,5'd0};state<=B_REQ;end
            else state<=DRAIN;
          end else if(is_w)w_number<=w_number+1'b1;
          else begin
            odd<=!odd;
            if(odd)begin
              if(x_row==98)begin pair<=pair+1'b1;x_row<=0;stripe<=0;tile<=0;end
              else begin x_row<=x_row+1'b1;
                if(stripe==STRIPES-1)begin stripe<=0;tile<=tile+1'b1;end else stripe<=stripe+1'b1;
              end
            end
          end
        end else if(remaining==0 && !pending)begin error<=1;state<=DRAIN;end
      end
      B_REQ:if(mem_ready)state<=B_WAIT;
      B_WAIT:if(ack)begin
        if(ret_err)begin error<=2;state<=DRAIN;end
        else if(bias_index==7)state<=DRAIN;
        else begin bias_index<=bias_index+1'b1;addr<=addr+4;state<=B_REQ;end
      end
      DRAIN:begin if(ack)pending<=0;if(!pending&&!emit)state<=FINISH;end
      FINISH:state<=IDLE;
      default:state<=IDLE;
    endcase
  end
endmodule

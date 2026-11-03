// SPDX-License-Identifier: MIT
// A single non-speculative ICB stream. All reads and writes finish with an
// actual response. X, W and Y jobs never share the external port concurrently.
module kwt_legacy_dma # (parameter integer PACK_LOW_FIRST=1,STRIPES=4) (
  input wire clk,rst_n,start,input wire [1:0] job,input wire [4:0] group_index,
  input wire [31:0] xb,wb,bb,yb,input wire compact,
  output wire done, output reg [1:0] error,
  output reg mem_valid,mem_read,output reg [31:0] mem_addr,mem_wdata,input wire mem_ready,
  input wire ret_valid,ret_err,input wire [31:0] ret_rdata,output wire ret_ready,
  output wire x_write,output reg [1:0] x_stripe,output reg [5:0] x_tile,output wire [4:0] x_pair,
  output wire [31:0] canonical,output wire w_write,b_write,output wire page,
  output wire [7:0] w_index,output wire [2:0] b_index,
  output wire y_read,output wire [6:0] y_rd_addr,input wire [127:0] y_vector
);
  localparam JOB_X=0,JOB_W=1,JOB_Y=2;
  localparam IDLE=0,READ_REQ=1,READ_WAIT=2,Y_READ=3,Y_DELTA=4,Y_PACK=5,
             WRITE_REQ=6,WRITE_WAIT=7,TAG_REQ=8,TAG_WAIT=9,FINISH=10,Y_LATCH=11;
  reg [6:0] y_row;
  reg [127:0] sampled_y;
  reg [3:0] state;
  reg [1:0] kind;
  reg [4:0] group_q;
  reg [11:0] index_q;
  reg bias_phase;
  reg [127:0] previous,payload;
  reg [1:0] mode_q,word_q;
  reg [31:0] tags;
  wire [1:0] mode;wire [127:0] packed_y;
  wire [31:0] logical_word=(state==TAG_REQ) ? tags : payload[32*word_q+:32];
  assign done=state==FINISH;
  assign ret_ready=rst_n && (state==READ_WAIT || state==WRITE_WAIT || state==TAG_WAIT);
  wire good_read=rst_n && state==READ_WAIT && ret_valid && !ret_err;
  assign x_write=good_read && kind==JOB_X;
  assign w_write=good_read && kind==JOB_W && !bias_phase;
  assign b_write=good_read && kind==JOB_W && bias_phase;
  assign x_pair=index_q[4:0];assign w_index=index_q[7:0];assign b_index=index_q[2:0];
  assign page=group_q[0];
  // Read the following local row while its predecessor writes on ICB.
  // The alternate result page is immutable for the duration of this DMA job.
  wire lookahead=state==WRITE_REQ && mem_ready && word_q==mode_q && y_row!=98;
  assign y_read=rst_n && (state==Y_READ || lookahead);
  assign y_rd_addr=lookahead ? y_row+1'b1 : y_row;
  assign canonical=PACK_LOW_FIRST ? ret_rdata : {ret_rdata[15:0],ret_rdata[31:16]};
  kwt_row_pack codec(.clk(clk),.capture(state==Y_DELTA),.compact(compact),
    .current(sampled_y),.previous(previous),.mode(mode),.payload(packed_y));
  // 7 tag words for 99 rows in each of 32 groups; layout follows the data slots.
  wire [7:0] tag_index=({3'b0,group_q}<<3)-{3'b0,group_q}+{5'd0,y_row[6:4]};
  always @* begin
    mem_valid=0;mem_read=1;mem_addr=0;mem_wdata=0;
    case(state)
      READ_REQ: begin
        mem_valid=rst_n;
        if(kind==JOB_X)mem_addr=xb+{18'd0,index_q,2'b00};
        else if(bias_phase)mem_addr=bb+{22'd0,group_q,index_q[2:0],2'b00};
        else mem_addr=wb+{17'd0,index_q[7:2],group_q,index_q[1:0],2'b00};
      end
      WRITE_REQ,TAG_REQ: begin
        mem_valid=rst_n;mem_read=0;
        if(state==TAG_REQ)mem_addr=yb+32'd50688+{22'd0,tag_index,2'b00};
        else mem_addr=yb+{16'd0,y_row,group_q,word_q,2'b00};
        mem_wdata=PACK_LOW_FIRST ? logical_word : {logical_word[15:0],logical_word[31:16]};
      end
      default:begin end
    endcase
  end
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin state<=IDLE;error<=0;kind<=0;group_q<=0;index_q<=0;bias_phase<=0;
      x_tile<=0;x_stripe<=0;y_row<=0;word_q<=0;mode_q<=0;end
    else case(state)
      IDLE: if(start)begin
        kind<=job;group_q<=group_index;index_q<=0;bias_phase<=0;x_tile<=0;x_stripe<=0;
        y_row<=0;word_q<=0;error<=0;state<=job==JOB_Y ? Y_READ : READ_REQ;
      end
      READ_REQ: if(mem_ready)state<=READ_WAIT;
      READ_WAIT: if(ret_valid)begin
        if(ret_err)begin error<=2;state<=FINISH;end
        else if(kind==JOB_X && index_q==3167)state<=FINISH;
        else if(kind==JOB_W && bias_phase && index_q==7)state<=FINISH;
        else begin
          if(kind==JOB_X && x_pair==31)begin
            if(x_stripe==STRIPES-1)begin x_stripe<=0;x_tile<=x_tile+1'b1;end else x_stripe<=x_stripe+1'b1;
          end
          if(kind==JOB_W && !bias_phase && index_q==255)begin bias_phase<=1;index_q<=0;end
          else index_q<=index_q+1'b1;
          state<=READ_REQ;
        end
      end
      Y_READ: state<=Y_LATCH;
      Y_LATCH: state<=Y_DELTA;
      Y_DELTA: state<=Y_PACK;
      Y_PACK: begin mode_q<=mode;word_q<=0;state<=WRITE_REQ;end
      WRITE_REQ: if(mem_ready)state<=WRITE_WAIT;
      WRITE_WAIT: if(ret_valid)begin
        if(ret_err)begin error<=3;state<=FINISH;end
        else if(word_q!=mode_q)begin word_q<=word_q+1'b1;state<=WRITE_REQ;end
        else if(compact && (y_row[3:0]==15 || y_row==98))state<=TAG_REQ;
        else if(y_row==98)state<=FINISH;
        else begin y_row<=y_row+1'b1;state<=Y_DELTA;end
      end
      TAG_REQ: if(mem_ready)state<=TAG_WAIT;
      TAG_WAIT: if(ret_valid)begin
        if(ret_err)begin error<=3;state<=FINISH;end
        else if(y_row==98)state<=FINISH;
        else begin y_row<=y_row+1'b1;state<=Y_DELTA;end
      end
      FINISH: state<=IDLE;
      default:state<=IDLE;
    endcase
  end
  always @(posedge clk)begin
    if(state==Y_LATCH || (state==WRITE_WAIT && word_q==mode_q && y_row!=98))
      sampled_y<=y_vector;
    if(state==IDLE && start)begin previous<=0;tags<=0;end
    else if(state==Y_DELTA)previous<=sampled_y;
    else if(state==Y_PACK)begin payload<=packed_y;tags[2*y_row[3:0]+:2]<=mode;end
    else if(state==TAG_WAIT && ret_valid)tags<=0;
  end
endmodule

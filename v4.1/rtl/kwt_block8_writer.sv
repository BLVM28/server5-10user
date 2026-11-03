// SPDX-License-Identifier: MIT
// The producer holds one encoded row until the consumer takes it. It then
// prepares the next row in parallel with both acknowledged data writes.
module kwt_block8_writer #(parameter integer PACK_LOW_FIRST=1)(
  input wire clk,rst_n,start,input wire [4:0] group_index,input wire [31:0] yb,
  output wire done,output reg [1:0] error,
  output wire mem_valid,output wire [31:0] addr,wdata,input wire mem_ready,
  input wire ret_valid,ret_err,output wire ret_ready,
  output wire y_read,output wire [6:0] y_addr,input wire [127:0] y_vector
);
  localparam IDLE=0,PICK=1,ISSUE=2,WAIT_RSP=3,FINISH=4;
  localparam STOP=0,READ_ROW=1,CAPTURE=2,ENCODING=3,FULL=4;
  reg [2:0] state,producer;
  reg [1:0] part;
  reg [6:0] row_n,fill_row;
  reg [63:0] payload,slot;
  reg [3:0] slot_shift;
  reg [31:0] tags,data_addr,tag_addr,tag_base;
  reg [10:0] tag_offset;
  wire encoded;wire [63:0] bytes;wire [3:0] exponent;
  assign done=state==FINISH;
  assign mem_valid=rst_n && state==ISSUE;assign ret_ready=rst_n && state==WAIT_RSP;
  assign addr=part==2 ? tag_addr : data_addr;
  wire [31:0] logical_data=part==2 ? tags : (part==1 ? payload[63:32] : payload[31:0]);
  assign wdata=PACK_LOW_FIRST ? logical_data : {logical_data[15:0],logical_data[31:16]};
  assign y_read=rst_n && producer==READ_ROW;assign y_addr=fill_row;
  kwt_block8_encoder enc(.clk(clk),.rst_n(rst_n),.valid(producer==CAPTURE),.values(y_vector),
    .out_valid(encoded),.bytes(bytes),.exponent(exponent));
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin producer<=STOP;fill_row<=0;end
    else if(start)begin fill_row<=0;producer<=READ_ROW;end
    else if(done || (state==WAIT_RSP && ret_valid && ret_err))producer<=STOP;
    else case(producer)
      READ_ROW: producer<=CAPTURE;
      CAPTURE: producer<=ENCODING;
      ENCODING:if(encoded)producer<=FULL;
      FULL:if(state==PICK)begin
        if(fill_row==98)producer<=STOP;
        else begin fill_row<=fill_row+1'b1;producer<=READ_ROW;end
      end
      default:producer<=STOP;
    endcase
  end
  always @(posedge clk)begin
    if(encoded)begin slot<=bytes;slot_shift<=exponent;end
    if(start)begin tag_base<=yb+32'd25344;tag_offset<=11'd52*group_index;end
    if(state==PICK && row_n==0)tag_addr<=tag_base+{21'd0,tag_offset};
    else if(state==WAIT_RSP && ret_valid && part==2)tag_addr<=tag_addr+4;
    if(start || (state==WAIT_RSP && ret_valid && part==2)) tags<=0;
    else if(state==PICK && producer==FULL)tags[4*row_n[2:0]+:4]<=slot_shift;
    if(state==PICK && producer==FULL)payload<=slot;
  end
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin state<=IDLE;row_n<=0;part<=0;error<=0;data_addr<=0;end
    else case(state)
      IDLE:if(start)begin row_n<=0;part<=0;error<=0;state<=PICK;data_addr<=yb+{24'd0,group_index,3'd0};end
      PICK:if(producer==FULL)begin part<=0;state<=ISSUE;end
      ISSUE:if(mem_ready)state<=WAIT_RSP;
      WAIT_RSP:if(ret_valid)begin
        if(ret_err)begin error<=3;state<=FINISH;end
        else if(part==0)begin data_addr<=data_addr+4;part<=1;state<=ISSUE;end
        else if(part==1)begin
          data_addr<=data_addr+252;
          if(row_n[2:0]==7 || row_n==98)begin part<=2;state<=ISSUE;end
          else begin row_n<=row_n+1'b1;state<=PICK;end
        end else if(row_n==98)state<=FINISH;
        else begin row_n<=row_n+1'b1;state<=PICK;end
      end
      FINISH:state<=IDLE;
      default:state<=IDLE;
    endcase
  end
endmodule

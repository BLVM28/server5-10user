// SPDX-License-Identifier: MIT
// Q11 correction: fixed-width, row-major signed 16/F11 output. No entropy
// encoding, predictor, header or per-stream slot exists in shared output RAM.
// Preserve r8 numerical rounding (sy) and restore its low zero bits before store.
module kwt43_writer #(parameter PACK_LOW_FIRST=1)(
  input wire clk,rst_n,start,input wire [3:0] group_index,sy,
  input wire [63:0] keys,input wire [31:0] yb,
  output wire done,output reg [1:0] error,
  output wire mem_valid,output wire [31:0] addr,wdata,input wire mem_ready,
  input wire ret_valid,ret_err,output wire ret_ready,
  output wire y_read,output wire [6:0] y_addr,input wire [255:0] y_vector
);
  // keys is retained only for source-port compatibility; it has no effect on Y.
  localparam IDLE=0,READ_ROW=1,LATCH_ROW=2,FORM_WORD=3,SEND=4,WAIT_RSP=5,FINISH=6;
  reg [2:0] state,pair_index;
  reg [3:0] scale;
  reg [6:0] row;
  reg [255:0] current;
  reg [31:0] row_base,addr_q,data_q;
  function automatic [15:0] numeric_y(input signed [15:0] sample,input [3:0] shift);
    reg signed [16:0] twice;
    reg signed [15:0] base,ceiling,q;
    begin
      twice=$signed({sample,1'b0})>>>shift;
      base=$signed(twice[16:1]);
      ceiling=$signed(16'h7fff)>>>shift;
      q=base==ceiling?base:base+$signed({15'd0,twice[0]});
      numeric_y=q<<<shift;
    end
  endfunction
  wire [15:0] a=numeric_y($signed(current[32*pair_index+:16]),scale);
  wire [15:0] b=numeric_y($signed(current[32*pair_index+16+:16]),scale);
  assign y_read=rst_n&&state==READ_ROW;
  assign y_addr=row;
  assign mem_valid=rst_n&&state==SEND;
  assign addr=addr_q;
  assign wdata=data_q;
  assign ret_ready=rst_n&&(state==WAIT_RSP||(state==SEND&&mem_ready));
  assign done=rst_n&&state==FINISH;
  wire ack=ret_valid&&ret_ready;
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin
      state<=IDLE;pair_index<=0;scale<=0;row<=0;error<=0;
      row_base<=0;addr_q<=0;data_q<=0;current<=0;
    end else begin
      case(state)
        IDLE:if(start)begin
          scale<=sy;row<=0;pair_index<=0;error<=0;
          row_base<=yb+{23'd0,group_index,5'd0};
          addr_q<=yb+{23'd0,group_index,5'd0};state<=READ_ROW;
        end
        READ_ROW:state<=LATCH_ROW;
        LATCH_ROW:begin current<=y_vector;state<=FORM_WORD;end
        FORM_WORD:begin data_q<=PACK_LOW_FIRST?{b,a}:{a,b};state<=SEND;end
        SEND:if(mem_ready)state<=WAIT_RSP;
        WAIT_RSP:begin end
        FINISH:state<=IDLE;
        default:state<=IDLE;
      endcase
      // Single outstanding write: stop immediately on its error; finish only
      // after the last write response, including legal zero-latency responses.
      if(ack)begin
        if(ret_err)begin error<=3;state<=FINISH;end
        else if(pair_index==7)begin
          pair_index<=0;
          if(row==98)state<=FINISH;
          else begin
            row<=row+1'b1;row_base<=row_base+32'd512;
            addr_q<=row_base+32'd512;state<=READ_ROW;
          end
        end else begin pair_index<=pair_index+1'b1;addr_q<=addr_q+32'd4;state<=FORM_WORD;end
      end
    end
  end
endmodule

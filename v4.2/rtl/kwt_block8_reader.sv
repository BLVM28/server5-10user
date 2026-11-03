// SPDX-License-Identifier: MIT
// A physical header/payload stream is read cold. Two pairs are distributed
// independently of the next ICB command; X single-port writes need a gap.
module kwt_block8_reader # (parameter integer PACK_LOW_FIRST=1,STRIPES=4)(
  input wire clk,rst_n,start,weights,input wire [4:0] group_index,input wire [31:0] xb,wb,bb,
  output wire done,output reg [1:0] error,
  output wire mem_valid,output reg [31:0] addr,input wire mem_ready,
  input wire ret_valid,ret_err,input wire [31:0] ret_data,output wire ret_ready,
  output wire x_write,w_write,b_write,output wire [1:0] x_stripe,
  output wire [5:0] x_tile,output wire [4:0] x_pair,output wire [7:0] w_index,
  output wire [2:0] b_index,output wire [31:0] pair_data
);
  localparam IDLE=0,ALIGN=1,REQ=2,WAIT_RSP=3,DRAIN=4,FINISH=5;
  localparam HEADER=0,DATA=1,BIAS=2;
  reg [2:0] state;
  reg [1:0] kind,phase;
  reg is_w,stored_w;
  reg [4:0] group_q;
  reg [6:0] word_n,stored_word;
  reg [1:0] stripe,stored_stripe;
  reg [5:0] tile,stored_tile;
  reg [31:0] header,data_q;
  reg [15:0] shifts_q;
  wire [31:0] canon=PACK_LOW_FIRST ? ret_data : {ret_data[15:0],ret_data[31:16]};
  wire [7:0] bad_nibble;
  genvar n;generate for(n=0;n<8;n=n+1)begin: validate
    assign bad_nibble[n]=canon[4*n+:4]>8;
  end endgenerate
  wire bad_header=is_w ? (|bad_nibble) : ((|canon[31:4])||bad_nibble[0]);
  assign done=state==FINISH;assign mem_valid=rst_n && state==REQ;
  assign ret_ready=rst_n && state==WAIT_RSP && (kind!=DATA || phase==0);
  wire accept=ret_valid && ret_ready;
  wire sending=(phase==1 || phase==3) && rst_n;
  assign x_write=sending && !stored_w;
  assign w_write=sending && stored_w;
  assign b_write=accept && !ret_err && kind==BIAS;
  assign x_stripe=stored_stripe;assign x_tile=stored_tile;
  assign x_pair={stored_word[3:0],phase==3};assign w_index={stored_word,phase==3};
  assign b_index=word_n[2:0];
  wire [15:0] pair_bytes=phase==3 ? data_q[31:16] : data_q[15:0];
  wire [7:0] pair_shift=phase==3 ? shifts_q[15:8] : shifts_q[7:0];
  generate for(n=0;n<2;n=n+1)begin: expand
    wire [7:0] m=pair_bytes[8*n+:8];
    wire [15:0] extended={{8{m[7]}},m};
    assign pair_data[16*n+:16]=extended<<pair_shift[4*n+:4];
  end endgenerate
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)phase<=0;
    else if(accept && !ret_err && kind==DATA)phase<=1;
    else if(phase!=0)phase<=phase+1'b1;
  end
  always @(posedge clk)begin
    if(accept && !ret_err && kind==HEADER)header<=canon;
    if(accept && !ret_err && kind==DATA)begin
      data_q<=canon;stored_word<=word_n;stored_w<=is_w;stored_tile<=tile;stored_stripe<=stripe;
      shifts_q<=is_w ? (word_n[0] ? header[31:16] : header[15:0]) : {4{header[3:0]}};
    end
  end
  always @(posedge clk or negedge rst_n)begin
    if(!rst_n)begin state<=IDLE;error<=0;addr<=0;kind<=HEADER;
      is_w<=0;group_q<=0;tile<=0;stripe<=0;word_n<=0;end
    else case(state)
      IDLE:if(start)begin
        error<=0;is_w<=weights;group_q<=group_index;word_n<=0;tile<=0;stripe<=0;kind<=HEADER;
        addr<=weights ? wb+{18'd0,group_index,9'd0} : xb;
        state<=weights ? ALIGN : REQ;
      end
      ALIGN:begin addr<=addr+{25'd0,group_q,2'd0};state<=REQ;end
      REQ:if(mem_ready)state<=WAIT_RSP;
      WAIT_RSP:if(accept)begin
        if(ret_err || (kind==HEADER && bad_header))begin error<=ret_err ? 2 : 1;state<=DRAIN;end
        else begin
          addr<=addr+4;state<=REQ;
          case(kind)
            HEADER:begin kind<=DATA;word_n<=0;end
            DATA:if(is_w && word_n==127)begin
              kind<=BIAS;word_n<=0;addr<=bb+{22'd0,group_q,5'd0};
            end else if(!is_w && word_n==15)begin
              word_n<=0;kind<=HEADER;
              if(stripe==STRIPES-1)begin stripe<=0;tile<=tile+1'b1;end else stripe<=stripe+1'b1;
              if(tile==98/STRIPES && stripe==98%STRIPES)state<=DRAIN;
            end else word_n<=word_n+1'b1;
            BIAS:if(word_n==7)state<=DRAIN;else word_n<=word_n+1'b1;
          endcase
        end
      end
      DRAIN:if(phase==0)state<=FINISH;
      FINISH:state<=IDLE;
      default:state<=IDLE;
    endcase
  end
endmodule

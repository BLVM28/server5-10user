// SPDX-License-Identifier: MIT
// A single non-speculative ICB stream. All reads and writes finish with an
// actual response. X, W and Y jobs never share the external port concurrently.
module kwt_tile_dma # (parameter integer PACK_LOW_FIRST=1) (
  input wire clk,rst_n,start,input wire [1:0] job,input wire [4:0] group_index,
  input wire [31:0] xb,wb,bb,yb,input wire compact,fast,
  output wire done, output wire [1:0] error,
  output wire mem_valid,mem_read,output wire [31:0] mem_addr,mem_wdata,input wire mem_ready,
  input wire ret_valid,ret_err,input wire [31:0] ret_rdata,output wire ret_ready,
  output wire x_write,output wire [1:0] x_stripe,output wire [5:0] x_tile,output wire [4:0] x_pair,
  output wire [31:0] canonical,output wire w_write,b_write,output wire page,
  output wire [7:0] w_index,output wire [2:0] b_index,
  output wire y_read,output wire [6:0] y_rd_addr,input wire [127:0] y_vector
);
  wire ld,lv,lr,lrr,lx,lw,lb,lp,ly;
  wire [1:0] le,ls;wire [5:0] lt;wire [4:0] li;wire [7:0] lwi;wire [2:0] lbi;wire [6:0] lya;
  wire [31:0] la,lwd,lc;
  kwt_legacy_dma #(.PACK_LOW_FIRST(PACK_LOW_FIRST)) legacy(
    .clk(clk),.rst_n(rst_n),.start(start && !fast),.job(job),.group_index(group_index),
    .xb(xb),.wb(wb),.bb(bb),.yb(yb),.compact(compact),.done(ld),.error(le),
    .mem_valid(lv),.mem_read(lr),.mem_addr(la),.mem_wdata(lwd),.mem_ready(mem_ready && !fast),
    .ret_valid(ret_valid && !fast),.ret_err(ret_err),.ret_rdata(ret_rdata),.ret_ready(lrr),
    .x_write(lx),.x_stripe(ls),.x_tile(lt),.x_pair(li),.canonical(lc),.w_write(lw),.b_write(lb),
    .page(lp),.w_index(lwi),.b_index(lbi),.y_read(ly),.y_rd_addr(lya),.y_vector(y_vector));
  reg write_job,page_q;
  always @(posedge clk)if(start && fast)begin write_job<=job==2;page_q<=group_index[0];end
  wire rd,rv,rr,rx,rw,rb,wd,wv,wr,wy;
  wire [1:0] re,we,rs;wire [5:0] rt;wire [4:0] ri;wire [7:0] rwi;wire [2:0] rbi;
  wire [31:0] ra,rc,wa,wdata;wire [6:0] wya;
  kwt_block8_reader #(.PACK_LOW_FIRST(PACK_LOW_FIRST)) reader(
    .clk(clk),.rst_n(rst_n),.start(start && fast && job!=2),.weights(job==1),
    .group_index(group_index),.xb(xb),.wb(wb),.bb(bb),.done(rd),.error(re),
    .mem_valid(rv),.addr(ra),.mem_ready(mem_ready && fast && !write_job),
    .ret_valid(ret_valid && fast && !write_job),.ret_err(ret_err),.ret_data(ret_rdata),.ret_ready(rr),
    .x_write(rx),.w_write(rw),.b_write(rb),.x_stripe(rs),.x_tile(rt),.x_pair(ri),
    .w_index(rwi),.b_index(rbi),.pair_data(rc));
  kwt_block8_writer #(.PACK_LOW_FIRST(PACK_LOW_FIRST)) writer(
    .clk(clk),.rst_n(rst_n),.start(start && fast && job==2),.group_index(group_index),.yb(yb),
    .done(wd),.error(we),.mem_valid(wv),.addr(wa),.wdata(wdata),.mem_ready(mem_ready && fast && write_job),
    .ret_valid(ret_valid && fast && write_job),.ret_err(ret_err),.ret_ready(wr),
    .y_read(wy),.y_addr(wya),.y_vector(y_vector));
  // Inactive engines never issue commands. Gating by valid here also keeps
  // the ICB pins defined while the first job's type register is initialized.
  assign mem_valid=lv||rv||wv;
  assign mem_read=fast ? !write_job : lr;
  assign mem_addr=fast ? (write_job ? wa : ra) : la;
  assign mem_wdata=fast ? wdata : lwd;
  assign ret_ready=fast ? (write_job ? wr : rr) : lrr;
  assign done=ld||rd||wd;assign error=fast ? (write_job?we:re) : le;
  assign page=fast ? page_q : lp;
  assign x_write=lx||rx;assign x_stripe=fast ? rs : ls;assign x_tile=fast ? rt : lt;
  assign x_pair=fast ? ri : li;assign canonical=fast ? rc : lc;
  assign w_write=lw||rw;assign b_write=lb||rb;assign w_index=fast ? rwi : lwi;assign b_index=fast ? rbi : lbi;
  assign y_read=ly||wy;assign y_rd_addr=fast ? wya : lya;
endmodule

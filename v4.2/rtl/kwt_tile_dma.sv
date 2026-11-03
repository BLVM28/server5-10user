// SPDX-License-Identifier: MIT
// A single non-speculative ICB stream. All reads and writes finish with an
// actual response. X, W and Y jobs never share the external port concurrently.
module kwt_tile_dma # (parameter integer PACK_LOW_FIRST=1,STRIPES=4) (
  input wire clk,rst_n,start,input wire [1:0] job,input wire [4:0] group_index,
  input wire [31:0] xb,wb,bb,yb,input wire compact,fast,precision,input wire [11:0] scales,
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
  kwt_legacy_dma #(.PACK_LOW_FIRST(PACK_LOW_FIRST),.STRIPES(STRIPES)) legacy(
    .clk(clk),.rst_n(rst_n),.start(start && !fast && !precision),.job(job),.group_index(group_index),
    .xb(xb),.wb(wb),.bb(bb),.yb(yb),.compact(compact),.done(ld),.error(le),
    .mem_valid(lv),.mem_read(lr),.mem_addr(la),.mem_wdata(lwd),.mem_ready(mem_ready && !fast && !precision),
    .ret_valid(ret_valid && !fast && !precision),.ret_err(ret_err),.ret_rdata(ret_rdata),.ret_ready(lrr),
    .x_write(lx),.x_stripe(ls),.x_tile(lt),.x_pair(li),.canonical(lc),.w_write(lw),.b_write(lb),
    .page(lp),.w_index(lwi),.b_index(lbi),.y_read(ly),.y_rd_addr(lya),.y_vector(y_vector));
  reg write_job,page_q;
  always @(posedge clk)if(start && (fast||precision))begin write_job<=job==2;page_q<=group_index[0];end
  wire rd,rv,rr,rx,rw,rb,wd,wv,wr,wy;
  wire [1:0] re,we,rs;wire [5:0] rt;wire [4:0] ri;wire [7:0] rwi;wire [2:0] rbi;
  wire [31:0] ra,rc,wa,wdata;wire [6:0] wya;
  kwt_block8_reader #(.PACK_LOW_FIRST(PACK_LOW_FIRST),.STRIPES(STRIPES)) reader(
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
  wire ir_done,ir_valid,ir_ready,ix,iw,ib,oy_done,oy_valid,oy_read,oy_ready,oy_sram;
  wire [1:0] ir_error,oy_error,ix_stripe;wire [5:0] ix_tile;wire [4:0] ix_pair;wire [7:0] iw_index;wire [2:0] ib_index;
  wire [31:0] ir_addr,ir_pair,oy_addr,oy_data;wire [6:0] oy_row;
  kwt_rice_reader #(.PACK_LOW_FIRST(PACK_LOW_FIRST),.STRIPES(STRIPES)) rice_in(.clk(clk),.rst_n(rst_n),
    .start(start&&precision&&job!=2),.weights(job==1),.group_index(group_index),.sx(scales[3:0]),.sw(scales[7:4]),
    .xb(xb),.wb(wb),.bb(bb),.done(ir_done),.error(ir_error),.mem_valid(ir_valid),.addr(ir_addr),
    .mem_ready(mem_ready&&precision&&!write_job),.ret_valid(ret_valid&&precision&&!write_job),.ret_err(ret_err),
    .ret_data(ret_rdata),.ret_ready(ir_ready),.x_write(ix),.w_write(iw),.b_write(ib),.x_stripe(ix_stripe),
    .x_tile(ix_tile),.x_pair(ix_pair),.w_index(iw_index),.b_index(ib_index),.pair_data(ir_pair));
  kwt_rice_writer #(.PACK_LOW_FIRST(PACK_LOW_FIRST)) rice_out(.clk(clk),.rst_n(rst_n),
    .start(start&&precision&&job==2),.group_index(group_index),.sy(scales[11:8]),.wb(wb),.yb(yb),
    .done(oy_done),.error(oy_error),.mem_valid(oy_valid),.mem_read(oy_read),.addr(oy_addr),.wdata(oy_data),
    .mem_ready(mem_ready&&precision&&write_job),.ret_valid(ret_valid&&precision&&write_job),.ret_err(ret_err),
    .ret_data(ret_rdata),.ret_ready(oy_ready),.y_read(oy_sram),.y_addr(oy_row),.y_vector(y_vector));
  assign mem_valid=lv||rv||wv||ir_valid||oy_valid;
  assign mem_read=precision ? (!write_job||oy_read) : fast ? !write_job : lr;
  assign mem_addr=precision ? (write_job?oy_addr:ir_addr) : fast ? (write_job ? wa : ra) : la;
  assign mem_wdata=precision ? oy_data : fast ? wdata : lwd;
  assign ret_ready=precision ? (write_job?oy_ready:ir_ready) : fast ? (write_job ? wr : rr) : lrr;
  assign done=ld||rd||wd||ir_done||oy_done;assign error=precision ? (write_job?oy_error:ir_error) : fast ? (write_job?we:re) : le;
  assign page=(fast||precision) ? page_q : lp;
  assign x_write=lx||rx||ix;assign x_stripe=precision?ix_stripe:(fast?rs:ls);assign x_tile=precision?ix_tile:(fast?rt:lt);
  assign x_pair=precision?ix_pair:(fast?ri:li);assign canonical=precision?ir_pair:(fast?rc:lc);
  assign w_write=lw||rw||iw;assign b_write=lb||rb||ib;assign w_index=precision?iw_index:(fast?rwi:lwi);assign b_index=precision?ib_index:(fast?rbi:lbi);
  assign y_read=ly||wy||oy_sram;assign y_rd_addr=precision?oy_row:(fast?wya:lya);
endmodule

`timescale 1ns/1ps
// NICE interface integration with an adversarial ICB memory BFM, NOT an E203 SoC.
module tb_core_all_gate;
`ifndef KWT_PERIOD_NS
`define KWT_PERIOD_NS 6.666667
`endif
  localparam [31:0] BASE=32'h10000000,BYTES=32'h80000;
  localparam integer DI=128,XI=1024,WI=5120,BI=22528,YI=24576;
  localparam [31:0] DESC=BASE+DI*4,XBASE=BASE+XI*4,WBASE=BASE+WI*4,
    BBASE=BASE+BI*4,YBASE=BASE+YI*4;
`ifdef KWT_TEST_SWAP
  localparam integer PACK=0;
`else
  localparam integer PACK=1;
`endif
`ifdef KWT_TEST_W1024
  localparam integer WAW=10;
`else
  localparam integer WAW=7;
`endif
  reg nice_clk=0;always #(`KWT_PERIOD_NS/2.0) nice_clk=~nice_clk;
  reg nice_rst_n=0,nice_req_valid=0,nice_rsp_ready=0;
  reg [31:0] nice_req_inst=32'h8000607b,nice_req_rs1=DESC,nice_req_rs2=0;
  wire nice_active,nice_mem_holdup,nice_req_ready,nice_rsp_valid,nice_rsp_err;
  wire [31:0] nice_rsp_rdat,nice_icb_cmd_addr,nice_icb_cmd_wdata;
  wire nice_icb_cmd_valid,nice_icb_cmd_ready,nice_icb_cmd_read,nice_icb_rsp_ready;
  wire [1:0] nice_icb_cmd_size;
  reg nice_icb_rsp_valid=0,nice_icb_rsp_err=0;
  reg [31:0] nice_icb_rsp_rdata=0;
  reg [31:0] memory[0:131071],expected[0:12671],sat_expect[0:11];
  reg [39:0] expected_acc[0:25343];
  reg [31:0] rng=32'h20261101,held_addr,held_wdata,read_addr,write_data;
  reg held_read,pending=0,captured_read=1,captured_error=0,held_valid=0;
  reg [1:0] held_size;
  reg error_enable=0,check_mac=0;
  reg [31:0] error_addr=0;
  integer wait_count=0,read_acks=0,write_acks=0,transactions=0,mac_outputs=0;
  integer i,l,j,tests=0,start_writes,start_transactions,start_mac,idx;
  string dir;reg [31:0] frozen_result;reg frozen_error;
  reg compact,block8,prec;
  reg [31:0] params[0:11],reads_ref[0:11],writes_ref[0:11],expected_wire[0:16383],expected_decoded[0:12671];
  reg [15:0] group_words[0:31];
  reg [31:0] expected_block[0:6751],decoded_block[0:12671];
  integer selected_layer,first_layer,last_layer;
  kwt_nice_core dut(.*);
  assign nice_icb_cmd_ready=nice_rst_n&&!pending&&!nice_icb_rsp_valid&&(rng[2:0]!=0);

  always @(posedge nice_clk or negedge nice_rst_n) begin
    if(!nice_rst_n) begin
      rng<=#1.000 32'h20261101;pending<=#1.000 0;nice_icb_rsp_valid<=#1.000 0;nice_icb_rsp_err<=#1.000 0;
      nice_icb_rsp_rdata<=#1.000 0;wait_count<=#1.000 0;held_valid<=#1.000 0;
      read_acks<=#1.000 0;write_acks<=#1.000 0;transactions<=#1.000 0;mac_outputs<=#1.000 0;
    end else begin
      rng<=#1.000 {rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
      if(held_valid && (!nice_icb_cmd_valid || nice_icb_cmd_addr!==held_addr ||
        nice_icb_cmd_wdata!==held_wdata || nice_icb_cmd_read!==held_read || nice_icb_cmd_size!==held_size))
        $fatal(1,"ICB command changed under backpressure");
      held_valid<=#1.000 nice_icb_cmd_valid&&!nice_icb_cmd_ready;
      held_addr<=#1.000 nice_icb_cmd_addr;held_wdata<=#1.000 nice_icb_cmd_wdata;
      held_read<=#1.000 nice_icb_cmd_read;held_size<=#1.000 nice_icb_cmd_size;
      if(nice_icb_cmd_valid&&nice_icb_cmd_ready) begin
        if(nice_icb_cmd_size!==2'b10 || nice_icb_cmd_addr[1:0]!=0 ||
          nice_icb_cmd_addr<BASE || nice_icb_cmd_addr>=BASE+BYTES)
          $fatal(1,"invalid bus command %h",nice_icb_cmd_addr);
        if(!nice_icb_cmd_read && (nice_icb_cmd_addr<YBASE || nice_icb_cmd_addr>=YBASE+(prec?65536:block8?27008:(compact?51584:50688))))
          $fatal(1,"write outside output region");
        pending<=#1.000 1;wait_count<=#1.000 rng[5:3];read_addr<=#1.000 nice_icb_cmd_addr;
        captured_read<=#1.000 nice_icb_cmd_read;write_data<=#1.000 nice_icb_cmd_wdata;
        captured_error<=#1.000 error_enable&&nice_icb_cmd_addr==error_addr;
        transactions<=#1.000 transactions+1;
      end
      if(pending) begin
        if(wait_count==0) begin
          pending<=#1.000 0;nice_icb_rsp_valid<=#1.000 1;nice_icb_rsp_err<=#1.000 captured_error;
          nice_icb_rsp_rdata<=#1.000 memory[(read_addr-BASE)>>2];
          if(!captured_read&&!captured_error) memory[(read_addr-BASE)>>2]<=#1.000 write_data;
        end else wait_count<=#1.000 wait_count-1;
      end
      if(nice_icb_rsp_valid&&nice_icb_rsp_ready) begin
        nice_icb_rsp_valid<=#1.000 0;
        if(captured_read)read_acks<=#1.000 read_acks+1;else write_acks<=#1.000 write_acks+1;
      end

    end
  end

  task reset_all;
    begin @(posedge nice_clk);#1.000;nice_rst_n=0;nice_req_valid=0;nice_rsp_ready=0;check_mac=0;
      repeat(4)@(posedge nice_clk);#1.000;nice_rst_n=1;
      @(posedge nice_clk);#1.000;if(!nice_req_ready||nice_rsp_valid||nice_icb_cmd_valid)$fatal(1,"bad reset state");end
  endtask
  task prepare(input integer layer);
    integer a;
    begin
      for(a=0;a<131072;a=a+1)memory[a]=32'h5a5aa5a5;
      $readmemh($sformatf("%s/layer%02d_x.hex",dir,layer),memory,XI,XI+(prec?4095:block8?1682:3167));
      $readmemh($sformatf("%s/layer%02d_w.hex",dir,layer),memory,WI,WI+(prec?16383:block8?4127:8191));
      $readmemh($sformatf("%s/layer%02d_b.hex",dir,layer),memory,BI,BI+255);
      $readmemh($sformatf("%s/layer%02d_y.hex",dir,layer),expected);
      $readmemh($sformatf("%s/layer%02d_acc.hex",dir,layer),expected_acc);
      if(prec)begin
        $readmemh($sformatf("%s/layer%02d_groups.hex",dir,layer),group_words);
        $readmemh($sformatf("%s/layer%02d_wire.hex",dir,layer),expected_wire);
        $readmemh($sformatf("%s/layer%02d_decoded.hex",dir,layer),expected_decoded);
      end
      if(block8)begin
        $readmemh($sformatf("%s/layer%02d_wire.hex",dir,layer),expected_block);
        $readmemh($sformatf("%s/layer%02d_decoded.hex",dir,layer),decoded_block);
      end
      if(!PACK)begin
        for(a=XI;a<XI+(prec?4096:block8?1683:3168);a=a+1)memory[a]={memory[a][15:0],memory[a][31:16]};
        for(a=WI;a<WI+(prec?16384:block8?4128:8192);a=a+1)memory[a]={memory[a][15:0],memory[a][31:16]};
        for(a=0;a<12672;a=a+1)expected[a]={expected[a][15:0],expected[a][31:16]};
      end
      memory[DI]=32'h3154574b;memory[DI+1]=prec ? 32'h00010003 : block8 ? 32'h00010002 : compact ? 32'h00010001 : 32'h00010000;memory[DI+2]=layer;
      memory[DI+3]=XBASE;memory[DI+4]=WBASE;memory[DI+5]=BBASE;memory[DI+6]=YBASE;memory[DI+7]=prec?params[layer]:0;
      error_enable=0;check_mac=0;
      nice_req_inst=32'h8000607b;nice_req_rs1=DESC;nice_req_rs2=0;
    end
  endtask
  task launch;
    begin @(posedge nice_clk);#1.000;nice_req_valid=1;
      @(posedge nice_clk);if(!nice_req_ready)$fatal(1,"NICE not ready");
      @(posedge nice_clk);#1.000;nice_req_valid=0;nice_req_rs1=32'hdeadbeef;nice_req_rs2=32'hffffffff;
    end
  endtask
  task finish_task(input integer expected_status,input bit consume);
    integer a;
    begin
      wait(nice_rsp_valid);@(posedge nice_clk);#1.000;
      if(nice_rsp_rdat!==expected_status || nice_rsp_err!==(expected_status!=0))
        $fatal(1,"unexpected NICE status %h expected %h",nice_rsp_rdat,expected_status);
      if(pending||nice_icb_rsp_valid||nice_icb_cmd_valid||nice_mem_holdup)
        $fatal(1,"completion with transactions still pending");
      frozen_result=nice_rsp_rdat;frozen_error=nice_rsp_err;
      for(a=0;a<7;a=a+1)begin @(posedge nice_clk);#1.000;
        if(!nice_rsp_valid||nice_rsp_rdat!==frozen_result||nice_rsp_err!==frozen_error||nice_req_ready)
          $fatal(1,"NICE response lost during backpressure");end
      if(consume)begin nice_rsp_ready=1;@(posedge nice_clk);#1.000;nice_rsp_ready=0;end
    end
  endtask
  function automatic [31:0] canonical_word(input [31:0] x);
    canonical_word=PACK ? x : {x[15:0],x[31:16]};
  endfunction
  // Decode memory without observing the hardware encoder. Reconstruct every
  // int16 and compare against the original v2/v3.1 uncompressed golden words.
  task automatic check_packed(output integer writes);
    integer g,m,l,mode,width,j,slot,old[0:7],val,mask;
    reg [31:0] header_word,golden; reg [127:0] bits;
    begin
      writes=224;
      for(g=0;g<32;g=g+1)begin
        for(l=0;l<8;l=l+1)old[l]=0;
        for(m=0;m<99;m=m+1)begin
          header_word=canonical_word(memory[YI+12672+7*g+m/16]);
          mode=(header_word>>(2*(m%16)))&3;width=4*(mode+1);mask=(1<<width)-1;
          if(m==98 && (header_word>>6)!=0)$fatal(1,"nonzero tag padding");
          writes=writes+mode+1;slot=YI+m*128+g*4;bits=0;
          for(j=0;j<4;j=j+1)
            if(j<=mode)bits[32*j+:32]=canonical_word(memory[slot+j]);
            else if(memory[slot+j]!==32'h5a5aa5a5)$fatal(1,"unexpected unused-slot write");
          for(l=0;l<8;l=l+1)begin
            val=(bits>>(l*width))&mask;
            if(val & (1<<(width-1)))val=val-(1<<width);
            if(mode!=3)val=val+old[l];
            golden=canonical_word(expected[m*128+g*4+l/2]);
            if(val < -32768 || val>32767 || val[15:0]!==golden[16*(l%2)+:16])
              $fatal(1,"packed mismatch row=%0d group=%0d lane=%0d tag=%0d value=%0d",m,g,l,mode,val);
            old[l]=val;
          end
        end
      end
    end
  endtask
  // Independent pin-level decoder. It also checks the never-written words in every slot.
  task automatic check_precision(input integer layer,output integer writes);
    integer g,l,m,n,start,at,k,q,zz,val,bits,scale,old[0:7],a,symbol,limit;
    reg [63:0] win;
    reg [31:0] hdr,lo,hi,decoded;
    begin
      writes=0;scale=params[layer][11:8];
      for(g=0;g<32;g=g+1)begin
        start=512*g;n=group_words[g];writes=writes+n;
        if(n<2 || n>512)$fatal(1,"bad reference length");
        for(a=0;a<512;a=a+1) begin
          if(a<n && canonical_word(memory[YI+start+a])!==expected_wire[start+a])
            $fatal(1,"precision wire layer=%0d group=%0d word=%0d got=%h expected=%h",layer,g,a,canonical_word(memory[YI+start+a]),expected_wire[start+a]);
          if(a>=n && memory[YI+start+a]!==32'h5a5aa5a5)$fatal(1,"write into unused precision slot");
        end
        hdr=canonical_word(memory[YI+start]);at=0;limit=(n-1)*32;
        for(l=0;l<8;l=l+1)old[l]=0;
        for(m=0;m<99;m=m+1)for(l=0;l<8;l=l+1)begin
          lo=canonical_word(memory[YI+start+1+at/32]);
          hi=(at/32+2<n)?canonical_word(memory[YI+start+2+at/32]):0;
          win={hi,lo}>>(at%32);k=(hdr>>(4*l))&15;
          q=0;while(q<4 && win[q])q=q+1;
          if(q==4)begin
            bits=16-scale;symbol=(win>>4)&((1<<bits)-1);
            val=(symbol & (1<<(bits-1)))?symbol-(1<<bits):symbol;
            at=at+4+bits;
          end else begin
            zz=(q<<k)|((win>>(q+1))&((1<<k)-1));val=old[l]+((zz>>1)^(-(zz&1)));at=at+q+1+k;
          end
          old[l]=val;val=val<<<scale;a=m*256+8*g+l;decoded=expected_decoded[a/2];
          if(at>limit || val< -32768 || val>32767 || val[15:0]!==decoded[16*(a%2)+:16])
            $fatal(1,"precision decode mismatch layer=%0d group=%0d row=%0d lane=%0d",layer,g,m,l);
        end
        if((at+31)/32!=n-1)$fatal(1,"precision word count mismatch");
      end
      if(writes!=writes_ref[layer])$fatal(1,"precision write reference mismatch");
    end
  endtask
  task full_case(input integer layer,input bit consume);
    integer a,expected_writes;
    begin
      prepare(layer);check_mac=0;start_writes=write_acks;start_transactions=transactions;start_mac=mac_outputs;
      launch();
      repeat(10)@(posedge nice_clk);#1.000;
      nice_req_valid=1;@(posedge nice_clk);if(nice_req_ready)$fatal(1,"accepted command while busy");
      @(posedge nice_clk);#1.000;nice_req_valid=0;
      finish_task(0,consume);
      expected_writes=12672;
      if(prec)check_precision(layer,expected_writes);
      else if(block8)begin
        expected_writes=6752;
        for(a=0;a<6752;a=a+1)if(canonical_word(memory[YI+a])!==expected_block[a])$fatal(1,"Block8 wire mismatch %0d",a);
        for(a=0;a<25344;a=a+1)begin: decode
          integer m,g,s,v;reg [31:0] t,p;
          m=a/256;g=(a%256)/8;t=canonical_word(memory[YI+6336+13*g+m/8]);
          s=(t>>(4*(m%8)))&15;p=canonical_word(memory[YI+a/4]);v=(p>>(8*(a%4)))&255;
          if(v>=128)v=v-256;v=v<<<s;
          if(s>8 || v[15:0]!==decoded_block[a/2][16*(a%2)+:16])$fatal(1,"Block8 decoded mismatch %0d",a);
        end
      end else if(compact)check_packed(expected_writes);
      else for(a=0;a<12672;a=a+1)if(memory[YI+a]!==expected[a])$fatal(1,"wrong raw output");
      if(write_acks-start_writes!=expected_writes || transactions-start_transactions!=(prec?reads_ref[layer]:block8?6075:11624)+expected_writes)
        $fatal(1,"wrong gate write or transaction count");
      if(memory[YI-1]!==32'h5a5aa5a5||memory[YI+(prec?16384:block8?6752:(compact?12896:12672))]!==32'h5a5aa5a5)$fatal(1,"output guard overwritten");
      $display("matrix gate layer %0d PASS writes=%0d transactions=%0d",layer,write_acks-start_writes,transactions-start_transactions);
      check_mac=0;tests=tests+1;
    end
  endtask
  initial begin
    `ifdef KWT_SDF_MIN
    $sdf_annotate("mapped.sdf",dut,,"sdf_annotation.log","MINIMUM");
`else
    $sdf_annotate("mapped.sdf",dut,,"sdf_annotation.log","MAXIMUM");
`endif
    prec=$test$plusargs("PRECISION42");compact=$test$plusargs("PACKED_OUTPUT");block8=$test$plusargs("BLOCK8_OUTPUT");
    if($test$plusargs("ANNOTATION_ONLY"))begin
      #100;$display("ANNOTATION_PROBE PASS");$finish;
    end
    if(!$value$plusargs("VEC_DIR=%s",dir))$fatal(1,"VEC_DIR required");
    if(prec)begin $readmemh({dir,"/params.hex"},params);$readmemh({dir,"/reads.hex"},reads_ref);$readmemh({dir,"/writes.hex"},writes_ref);end
    first_layer=0;last_layer=11;
    if($value$plusargs("LAYER=%d",selected_layer))begin
      if(selected_layer<0||selected_layer>11)$fatal(1,"invalid LAYER");
      first_layer=selected_layer;last_layer=selected_layer;
    end
    reset_all();for(l=first_layer;l<=last_layer;l=l+1)full_case(l,1);
    $display("ALL PASS, %0d/%0d full-core SDF matrix",tests,last_layer-first_layer+1);$finish;
  end
  initial begin #200000000;$fatal(1,"system timeout");end
endmodule

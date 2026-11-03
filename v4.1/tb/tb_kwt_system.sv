`timescale 1ns/1ps
// NICE interface integration with an adversarial ICB memory BFM, NOT an E203 SoC.
module tb_kwt_system #(parameter COMPACT=0,FAST=0,IMMEDIATE=0);
  localparam YWORDS=FAST ? 6752 : (COMPACT ? 12896 : 12672);
  localparam READS=FAST ? 6075 : 11624;
  reg [31:0] expected_wire[0:6751],expected_decoded[0:12671];
  time launched; integer nice_cycles;
  localparam [31:0] BASE=32'h10000000,BYTES=32'h80000;
  localparam integer DI=128,XI=1024,WI=5120,BI=13312,YI=14336;
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
  reg nice_clk=0;always #5 nice_clk=~nice_clk;
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
  kwt_nice_core #(.MEM_BASE(BASE),.MEM_BYTES(BYTES),.W_BANK_AW(WAW),.PACK_LOW_FIRST(PACK)) dut(.*);
  assign nice_icb_cmd_ready=nice_rst_n&&!pending&&!nice_icb_rsp_valid&&(rng[2:0]!=0);

  always @(posedge nice_clk or negedge nice_rst_n) begin
    if(!nice_rst_n) begin
      rng<=32'h20261101;pending<=0;nice_icb_rsp_valid<=0;nice_icb_rsp_err<=0;
      nice_icb_rsp_rdata<=0;wait_count<=0;held_valid<=0;
      read_acks<=0;write_acks<=0;transactions<=0;mac_outputs<=0;
    end else begin
      rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
      if(held_valid && (!nice_icb_cmd_valid || nice_icb_cmd_addr!==held_addr ||
        nice_icb_cmd_wdata!==held_wdata || nice_icb_cmd_read!==held_read || nice_icb_cmd_size!==held_size))
        $fatal(1,"ICB command changed under backpressure");
      held_valid<=nice_icb_cmd_valid&&!nice_icb_cmd_ready;
      held_addr<=nice_icb_cmd_addr;held_wdata<=nice_icb_cmd_wdata;
      held_read<=nice_icb_cmd_read;held_size<=nice_icb_cmd_size;
      if(nice_icb_cmd_valid&&nice_icb_cmd_ready) begin
        if(nice_icb_cmd_size!==2'b10 || nice_icb_cmd_addr[1:0]!=0 ||
          nice_icb_cmd_addr<BASE || nice_icb_cmd_addr>=BASE+BYTES)
          $fatal(1,"invalid bus command %h",nice_icb_cmd_addr);
        if(!nice_icb_cmd_read && (nice_icb_cmd_addr<YBASE || nice_icb_cmd_addr>=YBASE+4*YWORDS))
          $fatal(1,"write outside output region");
        pending<=1;wait_count<=rng[5:3];read_addr<=nice_icb_cmd_addr;
        captured_read<=nice_icb_cmd_read;write_data<=nice_icb_cmd_wdata;
        captured_error<=error_enable&&nice_icb_cmd_addr==error_addr;
        transactions<=transactions+1;
      end
      if(pending) begin
        if(wait_count==0) begin
          pending<=0;nice_icb_rsp_valid<=1;nice_icb_rsp_err<=captured_error;
          nice_icb_rsp_rdata<=memory[(read_addr-BASE)>>2];
          if(!captured_read&&!captured_error) memory[(read_addr-BASE)>>2]<=write_data;
        end else wait_count<=wait_count-1;
      end
      if(nice_icb_rsp_valid&&nice_icb_rsp_ready) begin
        nice_icb_rsp_valid<=0;
        if(captured_read)read_acks<=read_acks+1;else write_acks<=write_acks+1;
      end
      if(dut.core.x_rv!==dut.core.w_rv)$fatal(1,"operand valid misalignment");
      if(dut.core.x_rv && !dut.core.mac_pr)$fatal(1,"unstallable read pipeline overflow");
      if(check_mac&&dut.core.result_commit) begin
        for(integer lane=0;lane<8;lane=lane+1) begin
          if(dut.core.mac_acc[40*lane+:40]!==expected_acc[dut.core.row_m*256+dut.core.group_n*8+lane])
            $fatal(1,"full-precision accumulator mismatch row=%d group=%d lane=%d",dut.core.row_m,dut.core.group_n,lane);
        end
        mac_outputs<=mac_outputs+8;
      end
    end
  end

  task reset_all;
    begin @(negedge nice_clk);nice_rst_n=0;nice_req_valid=0;nice_rsp_ready=0;check_mac=0;
      repeat(4)@(negedge nice_clk);nice_rst_n=1;
      @(negedge nice_clk);if(!nice_req_ready||nice_rsp_valid||nice_icb_cmd_valid)$fatal(1,"bad reset state");end
  endtask
  task prepare(input integer layer);
    integer a;
    begin
      for(a=0;a<131072;a=a+1)memory[a]=32'h5a5aa5a5;
      $readmemh($sformatf("%s/layer%02d_x.hex",dir,layer),memory,XI,XI+(FAST?1682:3167));
      $readmemh($sformatf("%s/layer%02d_w.hex",dir,layer),memory,WI,WI+(FAST?4127:8191));
      $readmemh($sformatf("%s/layer%02d_b.hex",dir,layer),memory,BI,BI+255);
      $readmemh($sformatf("%s/layer%02d_y.hex",dir,layer),expected);
      $readmemh($sformatf("%s/layer%02d_acc.hex",dir,layer),expected_acc);
      if(FAST)begin
        $readmemh($sformatf("%s/layer%02d_wire.hex",dir,layer),expected_wire);
        $readmemh($sformatf("%s/layer%02d_decoded.hex",dir,layer),expected_decoded);
      end
      if(!PACK)begin
        for(a=XI;a<XI+(FAST?1683:3168);a=a+1)memory[a]={memory[a][15:0],memory[a][31:16]};
        for(a=WI;a<WI+(FAST?4128:8192);a=a+1)memory[a]={memory[a][15:0],memory[a][31:16]};
        for(a=0;a<12672;a=a+1)expected[a]={expected[a][15:0],expected[a][31:16]};
      end
      memory[DI]=32'h3154574b;memory[DI+1]=FAST ? 32'h00010002 : COMPACT ? 32'h00010001 : 32'h00010000;memory[DI+2]=layer;
      memory[DI+3]=XBASE;memory[DI+4]=WBASE;memory[DI+5]=BBASE;memory[DI+6]=YBASE;memory[DI+7]=0;
      error_enable=0;check_mac=0;
      nice_req_inst=32'h8000607b;nice_req_rs1=DESC;nice_req_rs2=0;
    end
  endtask
  task launch;
    begin @(negedge nice_clk);nice_req_valid=1;
      @(posedge nice_clk);launched=$time;if(!nice_req_ready)$fatal(1,"NICE not ready");
      @(negedge nice_clk);nice_req_valid=0;nice_req_rs1=32'hdeadbeef;nice_req_rs2=32'hffffffff;
    end
  endtask
  task finish_task(input integer expected_status,input bit consume);
    integer a;
    begin
      wait(nice_rsp_valid);nice_cycles=($time-launched)/10;@(negedge nice_clk);
      if(nice_rsp_rdat!==expected_status || nice_rsp_err!==(expected_status!=0))
        $fatal(1,"unexpected NICE status %h expected %h",nice_rsp_rdat,expected_status);
      if(pending||nice_icb_rsp_valid||nice_icb_cmd_valid||nice_mem_holdup)
        $fatal(1,"completion with transactions still pending");
      frozen_result=nice_rsp_rdat;frozen_error=nice_rsp_err;
      for(a=0;a<7;a=a+1)begin @(negedge nice_clk);
        if(!nice_rsp_valid||nice_rsp_rdat!==frozen_result||nice_rsp_err!==frozen_error||nice_req_ready)
          $fatal(1,"NICE response lost during backpressure");end
      if(consume)begin nice_rsp_ready=1;@(negedge nice_clk);nice_rsp_ready=0;end
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
  task full_case(input integer layer,input bit consume);
    integer a,expected_writes;
    begin
      prepare(layer);check_mac=1;start_writes=write_acks;start_transactions=transactions;start_mac=mac_outputs;
      launch();
      repeat(10)@(negedge nice_clk);
      nice_req_valid=1;@(posedge nice_clk);if(nice_req_ready)$fatal(1,"accepted command while busy");
      @(negedge nice_clk);nice_req_valid=0;
      finish_task(0,consume);
      expected_writes=12672;
      if(FAST)begin
        expected_writes=6752;
        for(a=0;a<6752;a=a+1)if(canonical_word(memory[YI+a])!==expected_wire[a])
          $fatal(1,"Block8 wire mismatch layer %0d word %0d got %h exp %h",layer,a,canonical_word(memory[YI+a]),expected_wire[a]);
        for(a=0;a<25344;a=a+1) begin: decoded_check
          integer m,g,shift,value;
          reg [31:0] t,p;
          m=a/256;g=(a%256)/8;
          t=canonical_word(memory[YI+6336+13*g+m/8]);shift=(t>>(4*(m%8)))&15;
          p=canonical_word(memory[YI+a/4]);value=(p>>(8*(a%4)))&255;
          if(value>=128)value=value-256;
          value=value<<<shift;
          if(shift>8 || value[15:0]!==expected_decoded[a/2][16*(a%2)+:16])
            $fatal(1,"Block8 decoded mismatch layer %0d index %0d",layer,a);
        end
      end else if(COMPACT)check_packed(expected_writes);
      else for(a=0;a<12672;a=a+1)if(memory[YI+a]!==expected[a])
        $fatal(1,"matrix mismatch layer=%0d word=%0d",layer,a);
      if(write_acks-start_writes!=expected_writes || transactions-start_transactions!=READS+expected_writes || mac_outputs-start_mac!=25344)
        $fatal(1,"wrong transaction/MAC accounting %d %d %d",write_acks-start_writes,transactions-start_transactions,mac_outputs-start_mac);
      if(memory[YI-1]!==32'h5a5aa5a5 || memory[YI+YWORDS]!==32'h5a5aa5a5)$fatal(1,"output guard overwritten");
      if(dut.c_sat!==sat_expect[layer])$fatal(1,"saturation count mismatch");
      $display("matrix layer %0d PASS core_cycles=%0d writes=%0d",layer,dut.c_cycles,write_acks-start_writes);
      $display("NICE_TIME layer=%0d cycles=%0d reads=%0d writes=%0d compact=%0d",layer,nice_cycles,transactions-start_transactions-(write_acks-start_writes),write_acks-start_writes,FAST?2:COMPACT);
      check_mac=0;tests=tests+1;
    end
  endtask
  task abort_stage(input integer phase);
    begin prepare(0);launch();case(phase)
        3: wait(dut.core.x_write); 8: wait(dut.core.w_write); 12: wait(dut.core.operand_read);
        15: wait(dut.core.mem_valid && !dut.core.mem_read);
        default: $fatal(1,"unhandled test phase");
      endcase
      reset_all();tests=tests+1;end
  endtask
  initial begin
    if(!$value$plusargs("VEC_DIR=%s",dir))dir="../../vec";
    $readmemh({dir,"/matrix_sat.hex"},sat_expect);
    reset_all();
    for(l=0;l<12;l=l+1)full_case(l,1);
    prepare(0);memory[DI]=0;launch();finish_task('h12,1);tests=tests+1;
    prepare(0);memory[DI+2]=12;launch();finish_task(4,1);tests=tests+1;
    prepare(0);memory[DI+3]=XBASE+2;launch();finish_task(1,1);tests=tests+1;
    prepare(0);memory[DI+6]=XBASE;launch();finish_task(1,1);tests=tests+1;
    prepare(0);nice_req_rs1=DESC+2;launch();finish_task('h11,1);tests=tests+1;
    prepare(0);nice_req_inst=0;launch();finish_task('h10,1);tests=tests+1;
    prepare(0);error_enable=1;error_addr=DESC;launch();finish_task('h13,1);tests=tests+1;
    prepare(0);error_enable=1;error_addr=WBASE;launch();finish_task(2,1);tests=tests+1;
    prepare(0);error_enable=1;error_addr=YBASE;launch();finish_task(3,1);tests=tests+1;
    prepare(0);memory[DI+3]=32'hfffffff0;launch();finish_task(1,1);tests=tests+1;
    abort_stage(3);abort_stage(8);abort_stage(12);abort_stage(15);
    full_case(0,0);reset_all();tests=tests+1;
    full_case(11,1);
    if(FAST)begin
      prepare(0);memory[XI]=32'hffffffff;launch();finish_task(1,1);
      prepare(0);memory[WI]=32'h99999999;launch();finish_task(1,1);
      prepare(0);error_enable=1;error_addr=YBASE+27004;launch();finish_task(3,1);
      prepare(0);memory[DI+6]=BASE+BYTES-27004;launch();finish_task(1,1);
      $display("BLOCK8 GUARD PASS 4/4");
    end
    if(COMPACT)begin
      prepare(0);error_enable=1;error_addr=YBASE+51580;launch();finish_task(3,1);
      prepare(0);memory[DI+6]=BASE+BYTES-50688;launch();finish_task(1,1);
      $display("COMPACT GUARD PASS 2/2 last tag error and enlarged aperture");
    end
    $display("ALL PASS, %0d/29 NICE/matrix scenarios PACK=%0d WAW=%0d",tests,PACK,WAW);$finish;
  end
  initial begin #200000000;$fatal(1,"system timeout");end
endmodule

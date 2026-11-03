`timescale 1ns/1ps
// NICE interface integration with an adversarial ICB memory BFM, NOT an E203 SoC.
module tb_kwt_overlap;
  integer overlap_cycles=0,held_mac_cycles=0;
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
  integer concurrent_reads=0, concurrent_results=0, finished_wait=0;
  kwt_nice_core #(.MEM_BASE(BASE),.MEM_BYTES(BYTES),.W_BANK_AW(WAW),.PACK_LOW_FIRST(PACK)) dut(.*);
  assign nice_icb_cmd_ready=nice_rst_n&&!pending&&!nice_icb_rsp_valid&&(rng[2:0]!=0);

  always @(posedge nice_clk or negedge nice_rst_n) begin
    if(!nice_rst_n) begin
      rng<=32'h20261101;pending<=0;nice_icb_rsp_valid<=0;nice_icb_rsp_err<=0;
      nice_icb_rsp_rdata<=0;wait_count<=0;held_valid<=0;
      read_acks<=0;write_acks<=0;transactions<=0;mac_outputs<=0;
    end else begin
      if(dut.core.operand_read && dut.core.w_write)begin
        if(dut.core.dma_page==dut.core.group_n[0])$fatal(1,"active W page overwritten");
        concurrent_reads=concurrent_reads+1;
      end
      if(dut.core.result_commit && dut.core.y_read)begin
        if(dut.core.dma_page==dut.core.group_n[0])$fatal(1,"active Y page overwritten");
        concurrent_results=concurrent_results+1;
      end
      if(dut.core.compute_done && dut.core.state==dut.core.NEXT_WAIT)finished_wait=finished_wait+1;
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
        if(!nice_icb_cmd_read && (nice_icb_cmd_addr<YBASE || nice_icb_cmd_addr>=YBASE+50688))
          $fatal(1,"write outside output region");
        pending<=1;wait_count<=(dut.core.state==dut.core.NEXT_WAIT && dut.core.group_n==0 ? 105 :
                                 (transactions%97==0 ? 128 : rng[5:3]));
        read_addr<=nice_icb_cmd_addr;
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
      $readmemh($sformatf("%s/layer%02d_x.hex",dir,layer),memory,XI,XI+3167);
      $readmemh($sformatf("%s/layer%02d_w.hex",dir,layer),memory,WI,WI+8191);
      $readmemh($sformatf("%s/layer%02d_b.hex",dir,layer),memory,BI,BI+255);
      $readmemh($sformatf("%s/layer%02d_y.hex",dir,layer),expected);
      $readmemh($sformatf("%s/layer%02d_acc.hex",dir,layer),expected_acc);
      if(!PACK)begin
        for(a=XI;a<XI+3168;a=a+1)memory[a]={memory[a][15:0],memory[a][31:16]};
        for(a=WI;a<WI+8192;a=a+1)memory[a]={memory[a][15:0],memory[a][31:16]};
        for(a=0;a<12672;a=a+1)expected[a]={expected[a][15:0],expected[a][31:16]};
      end
      memory[DI]=32'h3154574b;memory[DI+1]=32'h00010000;memory[DI+2]=layer;
      memory[DI+3]=XBASE;memory[DI+4]=WBASE;memory[DI+5]=BBASE;memory[DI+6]=YBASE;memory[DI+7]=0;
      error_enable=0;check_mac=0;
      nice_req_inst=32'h8000607b;nice_req_rs1=DESC;nice_req_rs2=0;
    end
  endtask
  task launch;
    begin @(negedge nice_clk);nice_req_valid=1;
      @(posedge nice_clk);if(!nice_req_ready)$fatal(1,"NICE not ready");
      @(negedge nice_clk);nice_req_valid=0;nice_req_rs1=32'hdeadbeef;nice_req_rs2=32'hffffffff;
    end
  endtask
  task finish_task(input integer expected_status,input bit consume);
    integer a;
    begin
      wait(nice_rsp_valid);@(negedge nice_clk);
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
  task full_case(input integer layer,input bit consume);
    integer a;
    begin
      prepare(layer);check_mac=1;start_writes=write_acks;start_transactions=transactions;start_mac=mac_outputs;
      launch();
      repeat(10)@(negedge nice_clk);
      nice_req_valid=1;@(posedge nice_clk);if(nice_req_ready)$fatal(1,"accepted command while busy");
      @(negedge nice_clk);nice_req_valid=0;
      finish_task(0,consume);
      if(write_acks-start_writes!=12672 || transactions-start_transactions!=24296 || mac_outputs-start_mac!=25344)
        $fatal(1,"wrong transaction/MAC accounting %d %d %d",write_acks-start_writes,transactions-start_transactions,mac_outputs-start_mac);
      for(a=0;a<12672;a=a+1)if(memory[YI+a]!==expected[a])
        $fatal(1,"matrix layer=%d word=%d actual=%h expected=%h",layer,a,memory[YI+a],expected[a]);
      if(memory[YI-1]!==32'h5a5aa5a5||memory[YI+12672]!==32'h5a5aa5a5)$fatal(1,"output guard overwritten");
      if(dut.c_sat!==sat_expect[layer])$fatal(1,"saturation count mismatch");
      $display("matrix layer %0d PASS core_cycles=%0d writes=%0d",layer,dut.c_cycles,write_acks-start_writes);
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
    prepare(0);launch();wait(dut.core.state==dut.core.NEXT_WAIT && dut.core.dma.state==dut.core.dma.READ_WAIT);reset_all();
    prepare(0);error_enable=1;error_addr=WBASE+16;launch();finish_task(2,1);
    full_case(0,1);
    prepare(0);error_enable=1;error_addr=YBASE+4;launch();finish_task(3,1);tests=tests+1;
    full_case(11,1); // Must recover without global reset after aborting prefetch.
    abort_stage(15);
    full_case(0,1);
    if(concurrent_reads==0 || concurrent_results==0 || finished_wait==0)$fatal(1,"page ownership or slow-DMA scenario not covered");
    $display("PAGE PASS 2/2 reset/read error; weight_overlap=%0d output_overlap=%0d delayed_dma=%0d",concurrent_reads,concurrent_results,finished_wait);
    $display("ALL PASS, %0d/5 overlap/error-recovery scenarios",tests);$finish;
  end
  initial begin #200000000;$fatal(1,"system timeout");end
endmodule

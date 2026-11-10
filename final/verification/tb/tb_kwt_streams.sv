// Independent full-interface verification. MODE 0 models a one-cycle,
// one-entry SRAM endpoint; MODE 1 preserves the v4.2 random wait stress.
`timescale 1ns/1ps
module tb_kwt_streams #(parameter BUS_MODE=0);
  localparam [31:0] BASE=32'h10000000,BYTES=32'h80000;
  localparam DI=128,XI=1024,WI=5120,BI=22528,YI=24576;
  localparam [31:0] DESC=BASE+4*DI,XBASE=BASE+4*XI,WBASE=BASE+4*WI,BBASE=BASE+4*BI,YBASE=BASE+4*YI;
`ifdef KWT_TEST_SWAP
  localparam PACK=0;
`else
  localparam PACK=1;
`endif
  reg nice_clk=0,nice_rst_n=0,nice_req_valid=0,nice_rsp_ready=0;
  reg [31:0] nice_req_inst=32'h8000607b,nice_req_rs1=DESC,nice_req_rs2=0;
  wire nice_req_ready,nice_rsp_valid,nice_rsp_err,nice_active,nice_mem_holdup;
  wire [31:0] nice_rsp_rdat,nice_icb_cmd_addr,nice_icb_cmd_wdata,nice_icb_rsp_rdata;
  wire nice_icb_cmd_valid,nice_icb_cmd_ready,nice_icb_cmd_read,nice_icb_rsp_valid,nice_icb_rsp_ready,nice_icb_rsp_err;
  wire [1:0] nice_icb_cmd_size;
  reg [31:0] memory[0:131071],expected_wire[0:16383],expected_decoded[0:12671];
  reg [39:0] expected_acc[0:25343];
  reg [31:0] sat_expect[0:11],params[0:11],reads_ref[0:11],writes_ref[0:11];
  reg [15:0] groups[0:63];
  reg error_enable=0,check_mac=0;
  reg [31:0] error_addr=0,rng=32'h20261101;
  integer transactions=0,read_acks=0,write_acks=0,mac_outputs=0,tests=0,layer;
  integer start_transactions,start_writes,start_mac,nice_cycles;
  time launched;
  reg held_valid=0,held_read;reg [31:0] held_addr,held_data;reg [1:0] held_size;
  string dir;
  kwt_nice_core #(.MEM_BASE(BASE),.MEM_BYTES(BYTES),.PACK_LOW_FIRST(PACK)) dut(.*);
`ifndef KWT_PERIOD_NS
`define KWT_PERIOD_NS 10.0
`endif
  always #(`KWT_PERIOD_NS/2.0) nice_clk=~nice_clk;
  integer clocks=0,launched_clock;
  always @(posedge nice_clk)clocks<=clocks+1;
  wire command=nice_icb_cmd_valid&&nice_icb_cmd_ready;
  wire response=nice_icb_rsp_valid&&nice_icb_rsp_ready;
  wire [16:0] index=(nice_icb_cmd_addr-BASE)>>2;
  generate if(BUS_MODE==2)begin: immediate
    assign nice_icb_cmd_ready=nice_rst_n;
    assign nice_icb_rsp_valid=command;
    assign nice_icb_rsp_rdata=memory[index];
    assign nice_icb_rsp_err=error_enable&&nice_icb_cmd_addr==error_addr;
    always @(posedge nice_clk)if(command&&!nice_icb_cmd_read&&!nice_icb_rsp_err)memory[index]<=nice_icb_cmd_wdata;
  end else if(BUS_MODE==0)begin: native_sram
    reg valid=0,error=0;reg [31:0] data=0;
    assign nice_icb_cmd_ready=nice_rst_n&&(!valid||nice_icb_rsp_ready);
    assign nice_icb_rsp_valid=valid;assign nice_icb_rsp_rdata=data;assign nice_icb_rsp_err=error;
    always @(posedge nice_clk or negedge nice_rst_n)begin
      if(!nice_rst_n)begin valid<=0;data<=0;error<=0;end
      else if(nice_icb_cmd_ready)begin
        valid<=nice_icb_cmd_valid;
        if(command)begin
          data<=memory[index];error<=error_enable&&nice_icb_cmd_addr==error_addr;
          if(!nice_icb_cmd_read&&!(error_enable&&nice_icb_cmd_addr==error_addr))memory[index]<=nice_icb_cmd_wdata;
        end
      end
    end
  end else if(BUS_MODE==3)begin: public_sram
    wire cs,we,clk_ram,active;
    wire [29:0] addr;wire [3:0] wem;wire [31:0] din;reg [31:0] dout=0;
    wire [16:0] mi=addr-(BASE>>2);
    sirv_sram_icb_ctrl #(.DW(32),.MW(4),.AW(32),.AW_LSB(2),.USR_W(1)) endpoint(
      .sram_ctrl_active(active),.tcm_cgstop(1'b0),
      .i_icb_cmd_valid(nice_icb_cmd_valid),.i_icb_cmd_ready(nice_icb_cmd_ready),
      .i_icb_cmd_read(nice_icb_cmd_read),.i_icb_cmd_addr(nice_icb_cmd_addr),
      .i_icb_cmd_wdata(nice_icb_cmd_wdata),.i_icb_cmd_wmask(4'hf),
      .i_icb_cmd_usr(error_enable&&nice_icb_cmd_addr==error_addr),
      .i_icb_rsp_valid(nice_icb_rsp_valid),.i_icb_rsp_ready(nice_icb_rsp_ready),
      .i_icb_rsp_rdata(nice_icb_rsp_rdata),.i_icb_rsp_usr(nice_icb_rsp_err),
      .ram_cs(cs),.ram_we(we),.ram_addr(addr),.ram_wem(wem),.ram_din(din),.ram_dout(dout),
      .clk_ram(clk_ram),.test_mode(1'b0),.clk(nice_clk),.rst_n(nice_rst_n));
    always @(posedge clk_ram)if(cs)begin
      dout<=memory[mi];
      if(we&&!(error_enable&&{addr,2'b00}==error_addr))
        for(integer byte_no=0;byte_no<4;byte_no=byte_no+1)
          if(wem[byte_no])memory[mi][byte_no*8+:8]<=din[byte_no*8+:8];
    end
  end else begin: random_wait
    reg pending=0,valid=0,error=0,captured_error=0,captured_read;
    reg [31:0] data=0,saved_addr,saved_data;
    integer waiting=0;
    assign nice_icb_cmd_ready=nice_rst_n&&!pending&&!valid&&(rng[2:0]!=0);
    assign nice_icb_rsp_valid=valid;assign nice_icb_rsp_rdata=data;assign nice_icb_rsp_err=error;
    always @(posedge nice_clk or negedge nice_rst_n)begin
      if(!nice_rst_n)begin pending<=0;valid<=0;error<=0;data<=0;waiting<=0;end
      else begin
        if(command)begin pending<=1;waiting<=rng[5:3];saved_addr<=nice_icb_cmd_addr;saved_data<=nice_icb_cmd_wdata;
          captured_read<=nice_icb_cmd_read;captured_error<=error_enable&&nice_icb_cmd_addr==error_addr;end
        if(pending)begin
          if(waiting==0)begin
            pending<=0;valid<=1;error<=captured_error;data<=memory[(saved_addr-BASE)>>2];
            if(!captured_read&&!captured_error)memory[(saved_addr-BASE)>>2]<=saved_data;
          end else waiting<=waiting-1;
        end
        if(response)valid<=0;
      end
    end
  end endgenerate
  reg response_is_read=1;
  always @(posedge nice_clk or negedge nice_rst_n)begin
    if(!nice_rst_n)begin rng<=32'h20261101;transactions<=0;read_acks<=0;write_acks<=0;mac_outputs<=0;held_valid<=0;response_is_read<=1;end
    else begin
      rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
      if(held_valid&&(!nice_icb_cmd_valid||nice_icb_cmd_addr!==held_addr||nice_icb_cmd_read!==held_read||
          nice_icb_cmd_wdata!==held_data||nice_icb_cmd_size!==held_size))$fatal(1,"command changed under backpressure");
      held_valid<=nice_icb_cmd_valid&&!nice_icb_cmd_ready;held_addr<=nice_icb_cmd_addr;held_data<=nice_icb_cmd_wdata;
      held_read<=nice_icb_cmd_read;held_size<=nice_icb_cmd_size;
      if(command)begin
        if(nice_icb_cmd_size!==2 || nice_icb_cmd_addr[1:0]!=0 || nice_icb_cmd_addr<BASE || nice_icb_cmd_addr>=BASE+BYTES)$fatal(1,"invalid bus request");
        if(!nice_icb_cmd_read&&(nice_icb_cmd_addr<YBASE||nice_icb_cmd_addr>=YBASE+65536))$fatal(1,"write outside Y");
        transactions<=transactions+1;response_is_read<=nice_icb_cmd_read;
      end
      if(response)begin
        if(BUS_MODE==2?nice_icb_cmd_read:response_is_read)read_acks<=read_acks+1;else write_acks<=write_acks+1;
      end
`ifndef KWT_GATE
      if(dut.core.x_rv!==dut.core.w_rv)$fatal(1,"operand alignment");
      if(check_mac&&dut.core.result_commit)begin
        for(integer l=0;l<16;l=l+1)if(dut.core.mac_acc[40*l+:40]!==expected_acc[dut.core.row_m*256+dut.core.group_n*16+l])
          $fatal(1,"sum mismatch row=%0d group=%0d lane=%0d got=%h expected=%h",dut.core.row_m,dut.core.group_n,l,dut.core.mac_acc[40*l+:40],expected_acc[dut.core.row_m*256+dut.core.group_n*16+l]);
        mac_outputs<=mac_outputs+16;
      end
`endif
    end
  end
  function automatic [31:0] canonical(input [31:0] word);
    canonical=PACK?word:{word[15:0],word[31:16]};
  endfunction
  task reset_all;
    begin
      @(negedge nice_clk);nice_rst_n=0;nice_req_valid=0;nice_rsp_ready=0;check_mac=0;
      repeat(4)@(negedge nice_clk);nice_rst_n=1;
      @(negedge nice_clk);if(!nice_req_ready||nice_rsp_valid||nice_icb_cmd_valid)$fatal(1,"reset");
    end
  endtask
  task prepare(input integer l);
    integer a;
    begin
      for(a=0;a<131072;a=a+1)memory[a]=32'h5a5aa5a5;
      $readmemh($sformatf("%s/layer%02d_x.hex",dir,l),memory,XI,XI+4095);
      $readmemh($sformatf("%s/layer%02d_w.hex",dir,l),memory,WI,WI+16383);
      $readmemh($sformatf("%s/layer%02d_b.hex",dir,l),memory,BI,BI+255);
      $readmemh($sformatf("%s/layer%02d_acc.hex",dir,l),expected_acc);
      $readmemh($sformatf("%s/layer%02d_wire.hex",dir,l),expected_wire);
      $readmemh($sformatf("%s/layer%02d_decoded.hex",dir,l),expected_decoded);
      $readmemh($sformatf("%s/layer%02d_groups.hex",dir,l),groups);
      if(!PACK)begin
        for(a=XI;a<XI+4096;a=a+1)memory[a]=canonical(memory[a]);
        for(a=WI;a<WI+16384;a=a+1)memory[a]=canonical(memory[a]);
      end
      memory[DI]=32'h3154574b;memory[DI+1]=32'h10004;memory[DI+2]=l;memory[DI+3]=XBASE;
      memory[DI+4]=WBASE;memory[DI+5]=BBASE;memory[DI+6]=YBASE;memory[DI+7]=params[l];
      nice_req_inst=32'h8000607b;nice_req_rs1=DESC;nice_req_rs2=0;error_enable=0;check_mac=0;
    end
  endtask
  task launch;
    begin
      @(negedge nice_clk);nice_req_valid=1;
      @(posedge nice_clk);if(!nice_req_ready)$fatal(1,"NICE busy");launched=$time;launched_clock=clocks;
      if($test$plusargs("POWER"))$dumpon;
      @(negedge nice_clk);nice_req_valid=0;nice_req_rs1=32'hdeadbeef;
    end
  endtask
  task finish(input integer status,input bit consume);
    reg [31:0] held;
    begin
      wait(nice_rsp_valid);nice_cycles=clocks-launched_clock;
      if($test$plusargs("POWER"))$dumpoff;@(negedge nice_clk);
      if(nice_rsp_rdat!==status||nice_rsp_err!==(status!=0))$fatal(1,"status %h expected %h",nice_rsp_rdat,status);
      if(nice_icb_cmd_valid||nice_icb_rsp_valid||nice_mem_holdup)$fatal(1,"unfinished transaction");
      held=nice_rsp_rdat;
      repeat(7)begin @(negedge nice_clk);if(!nice_rsp_valid||nice_rsp_rdat!==held||nice_req_ready)$fatal(1,"response backpressure");end
      if(consume)begin nice_rsp_ready=1;@(negedge nice_clk);nice_rsp_ready=0;end
    end
  endtask
  task check_output(input integer l);
    integer slot,at,r,j,a,n,bits,k,q,z,v,old[0:3],total,col,scale;
    reg [31:0] header,lo,hi,golden;
    reg [63:0] window;
    begin
      total=0;scale=params[l][11:8];
      for(slot=0;slot<64;slot=slot+1)begin
        n=groups[slot];total=total+n;
        for(a=0;a<256;a=a+1)begin
          if(a<n&&canonical(memory[YI+256*slot+a])!==expected_wire[256*slot+a])
            $fatal(1,"wire mismatch layer=%0d stream=%0d word=%0d got=%h exp=%h",l,slot,a,canonical(memory[YI+256*slot+a]),expected_wire[256*slot+a]);
          if(a>=n&&memory[YI+256*slot+a]!==32'h5a5aa5a5)$fatal(1,"unused slot modified");
        end
        header=canonical(memory[YI+256*slot]);if(header[31:16]!=0)$fatal(1,"Y header reserved bits");
        at=0;for(j=0;j<4;j=j+1)old[j]=0;
        for(r=0;r<99;r=r+1)for(j=0;j<4;j=j+1)begin
          lo=canonical(memory[YI+256*slot+1+at/32]);hi=at/32+2<n?canonical(memory[YI+256*slot+2+at/32]):0;
          window={hi,lo}>>(at%32);k=(header>>(4*j))&15;q=0;
          while(q<4&&window[q])q=q+1;
          if(q==4)begin
            bits=16-scale;v=(window>>4)&((1<<bits)-1);
            if(v&(1<<(bits-1)))v=v-(1<<bits);
            at=at+4+bits;
          end else begin z=(q<<k)|((window>>(q+1))&((1<<k)-1));v=old[j]+((z>>1)^(-(z&1)));at=at+q+1+k;end
          old[j]=v;v=v<<<scale;col=(slot/4)*16+(slot%4)+4*j;a=r*256+col;golden=expected_decoded[a/2];
          if(v< -32768||v>32767||v[15:0]!==golden[16*(a%2)+:16])$fatal(1,"decoded matrix mismatch");
        end
        if((at+31)/32!=n-1)$fatal(1,"Y word count");
      end
      if(total!=writes_ref[l])$fatal(1,"Y reference transactions");
    end
  endtask
  task full_case(input integer l,input bit consume);
    begin
      prepare(l);check_mac=1;start_writes=write_acks;start_transactions=transactions;start_mac=mac_outputs;
      launch();
      repeat(10)@(negedge nice_clk);
      nice_req_valid=1;@(posedge nice_clk);if(nice_req_ready)$fatal(1,"accepted while busy");
      @(negedge nice_clk);nice_req_valid=0;
      finish(0,consume);check_output(l);
      if(write_acks-start_writes!=writes_ref[l]||transactions-start_transactions!=reads_ref[l]+writes_ref[l])
        $fatal(1,"accounting %d %d %d",write_acks-start_writes,transactions-start_transactions,mac_outputs-start_mac);
      if(memory[YI-1]!==32'h5a5aa5a5||memory[YI+16384]!==32'h5a5aa5a5)$fatal(1,"guard");
`ifndef KWT_GATE
      if(mac_outputs-start_mac!=25344)$fatal(1,"MAC output count");
      if(dut.c_sat!==sat_expect[l])$fatal(1,"saturation count");
`endif
      if($test$plusargs("DUMP_RAM"))$writememh($sformatf("streams_layer%02d.hex",l),memory,YI,YI+16383);
      $display("NICE_TIME layer=%0d cycles=%0d reads=%0d writes=%0d mode=%0d",l,nice_cycles,reads_ref[l],write_acks-start_writes,BUS_MODE);
      check_mac=0;tests=tests+1;
    end
  endtask
`ifndef KWT_GATE
  task abort_stage(input integer phase);
    begin
      prepare(0);launch();
      case(phase)
        0:wait(dut.core.x_write);1:wait(dut.core.w_write);
        2:wait(dut.core.operand_read);3:wait(nice_icb_cmd_valid&&!nice_icb_cmd_read);
      endcase
      reset_all();tests=tests+1;
    end
  endtask
`endif
  initial begin
`ifdef KWT_GATE
`ifdef KWT_SDF_MIN
    $sdf_annotate("mapped.sdf",dut,,"sdf_annotation.log","MINIMUM");
`else
    $sdf_annotate("mapped.sdf",dut,,"sdf_annotation.log","MAXIMUM");
`endif
`endif
    if(!$value$plusargs("VEC_DIR=%s",dir))dir="../../vec";
    $readmemh({dir,"/matrix_sat.hex"},sat_expect);$readmemh({dir,"/params.hex"},params);
    $readmemh({dir,"/reads.hex"},reads_ref);$readmemh({dir,"/writes.hex"},writes_ref);
    reset_all();
    if($test$plusargs("POWER"))begin $dumpfile("task.vcd");$dumpvars(0,dut);$dumpoff;end
    if($value$plusargs("LAYER=%d",layer))begin
      if(layer<0||layer>11)$fatal(1,"invalid layer");
      full_case(layer,1);$display("ALL PASS, 1/1 complete pin-level matrix");$finish;
    end
    for(layer=0;layer<12;layer=layer+1)full_case(layer,1);
`ifndef KWT_GATE
    prepare(0);memory[DI]=0;launch();finish('h12,1);tests=tests+1;
    prepare(0);memory[DI+2]=12;launch();finish(4,1);tests=tests+1;
    prepare(0);memory[DI+3]=XBASE+2;launch();finish(1,1);tests=tests+1;
    prepare(0);memory[DI+6]=XBASE;launch();finish(1,1);tests=tests+1;
    prepare(0);nice_req_rs1=DESC+2;launch();finish('h11,1);tests=tests+1;
    prepare(0);nice_req_inst=0;launch();finish('h10,1);tests=tests+1;
    prepare(0);error_enable=1;error_addr=DESC;launch();finish('h13,1);tests=tests+1;
    prepare(0);error_enable=1;error_addr=WBASE;launch();finish(2,1);tests=tests+1;
    prepare(0);error_enable=1;error_addr=YBASE;launch();finish(3,1);tests=tests+1;
    prepare(0);memory[DI+3]=32'hfffffff0;launch();finish(1,1);tests=tests+1;
    abort_stage(0);abort_stage(1);abort_stage(2);abort_stage(3);
    full_case(0,0);reset_all();tests=tests+1;
    full_case(11,1);
    // Each of the four independently framed streams is checked, including error draining.
    for(integer s=0;s<4;s=s+1)begin
      prepare(0);memory[XI+1024*s]=0;launch();finish(1,1);
      prepare(0);memory[XI+1024*s]=canonical(canonical(memory[XI+1024*s])-1);launch();finish(1,1);
      prepare(0);memory[XI+1024*s]=canonical(canonical(memory[XI+1024*s])+1);launch();finish(1,1);
      prepare(0);error_enable=1;error_addr=WBASE+1024*s+4;launch();finish(2,1);
      prepare(0);error_enable=1;error_addr=YBASE+4*(256*(60+s)+groups[60+s]-1);launch();finish(3,1);
    end
    prepare(0);memory[DI+7]=32'h1000;launch();finish('h12,1);
    prepare(0);memory[DI+7]=32'h006;launch();finish('h12,1);
    prepare(0);memory[DI+6]=BASE+BYTES-65532;launch();finish(1,1);
    prepare(0);memory[DI+7]=32'h230;launch();finish('h12,1);
    prepare(0);memory[DI+7]=32'h221;launch();finish('h12,1);
    $display("STREAM GUARD PASS 25/25");
`endif
    $display("ALL PASS, %0d/29 NICE/matrix scenarios PACK=%0d MODE=%0d",tests,PACK,BUS_MODE);$finish;
  end
  initial begin #300000000;$fatal(1,"system timeout");end
endmodule

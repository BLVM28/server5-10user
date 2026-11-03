// Independent memory model: every accepted command returns its result on that edge.
`timescale 1ns/1ps
module tb_kwt_block8_immediate;
  localparam [31:0] BASE=32'h10000000;
  localparam DI=128,XI=1024,WI=5120,BI=13312,YI=14336;
  reg nice_clk=0,nice_rst_n=0,nice_req_valid=0,nice_rsp_ready=0;
  reg [31:0] nice_req_inst=32'h8000607b,nice_req_rs1=BASE+DI*4,nice_req_rs2=0;
  wire nice_active,nice_mem_holdup,nice_req_ready,nice_rsp_valid,nice_rsp_err;
  wire [31:0] nice_rsp_rdat,nice_icb_cmd_addr,nice_icb_cmd_wdata;
  wire nice_icb_cmd_valid,nice_icb_cmd_ready,nice_icb_cmd_read,nice_icb_rsp_ready;
  wire [1:0] nice_icb_cmd_size;
  reg [31:0] ram[0:131071],gold[0:6751];
  wire [16:0] index=(nice_icb_cmd_addr-BASE)>>2;
  assign nice_icb_cmd_ready=nice_rst_n;
  wire nice_icb_rsp_valid=nice_icb_cmd_valid && nice_icb_cmd_ready;
  wire nice_icb_rsp_err=0;wire [31:0] nice_icb_rsp_rdata=ram[index];
  kwt_nice_core #(.MEM_BASE(BASE),.MEM_BYTES(32'h80000)) dut(.*);
  always #5 nice_clk=~nice_clk;
  integer reads=0,writes=0,l,i;
  string dir,capture_dir;
  always @(posedge nice_clk)if(nice_icb_rsp_valid)begin
    if(!nice_icb_rsp_ready || nice_icb_cmd_size!=2 || nice_icb_cmd_addr[1:0]!=0)$fatal(1,"same-edge handshake");
    if(nice_icb_cmd_read)reads<=reads+1;
    else begin
      if(index<YI || index>=YI+6752)$fatal(1,"write aperture");
      if(nice_icb_cmd_wdata!==gold[index-YI])$fatal(1,"wrong physical write %0d",index-YI);
      ram[index]<=nice_icb_cmd_wdata;writes<=writes+1;
    end
  end
  initial begin
    if(!$value$plusargs("VEC_DIR=%s",dir))dir="../../vec";
    if(!$value$plusargs("CAPTURE_DIR=%s",capture_dir))capture_dir=".";
    repeat(4)@(negedge nice_clk);nice_rst_n=1;
    for(l=0;l<12;l=l+1)begin
      for(i=0;i<131072;i=i+1)ram[i]=32'h5a5aa5a5;
      $readmemh($sformatf("%s/layer%02d_x.hex",dir,l),ram,XI,XI+1682);
      $readmemh($sformatf("%s/layer%02d_w.hex",dir,l),ram,WI,WI+4127);
      $readmemh($sformatf("%s/layer%02d_b.hex",dir,l),ram,BI,BI+255);
      $readmemh($sformatf("%s/layer%02d_wire.hex",dir,l),gold);
      ram[DI]=32'h3154574b;ram[DI+1]=32'h10002;ram[DI+2]=l;ram[DI+3]=BASE+4*XI;
      ram[DI+4]=BASE+4*WI;ram[DI+5]=BASE+4*BI;ram[DI+6]=BASE+4*YI;ram[DI+7]=0;
      reads=0;writes=0;
      @(negedge nice_clk);nice_req_valid=1;
      @(posedge nice_clk);if(!nice_req_ready)$fatal(1,"not ready");
      @(negedge nice_clk);nice_req_valid=0;
      wait(nice_rsp_valid);@(negedge nice_clk);
      if(nice_rsp_err || nice_rsp_rdat!=0 || reads!=6075 || writes!=6752)$fatal(1,"response/accounting %d %d",reads,writes);
      for(i=0;i<6752;i=i+1)if(ram[YI+i]!==gold[i])$fatal(1,"address not delivered %d",i);
      $writememh($sformatf("%s/block8_layer%02d.hex",capture_dir,l),ram,YI,YI+6751);
      nice_rsp_ready=1;@(negedge nice_clk);nice_rsp_ready=0;
    end
    $display("ALL PASS, 12/12 same-edge full Block8 matrices");$finish;
  end
  initial begin #30000000;$fatal(1,"timeout");end
endmodule

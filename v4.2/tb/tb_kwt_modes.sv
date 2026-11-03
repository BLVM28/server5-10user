// Check live descriptor format changes and recovery on one NICE instance.
`timescale 1ns/1ps
module tb_kwt_modes;
  localparam [31:0] BASE=32'h10000000;
  localparam DI=128,XI=1024,WI=5120,BI=22528,YI=24576;
  reg nice_clk=0,nice_rst_n=0,nice_req_valid=0,nice_rsp_ready=0;
  reg [31:0] nice_req_inst=32'h8000607b,nice_req_rs1=BASE+DI*4,nice_req_rs2=0;
  wire nice_active,nice_mem_holdup,nice_req_ready,nice_rsp_valid,nice_rsp_err;
  wire [31:0] nice_rsp_rdat,nice_icb_cmd_addr,nice_icb_cmd_wdata;
  wire nice_icb_cmd_valid,nice_icb_cmd_ready,nice_icb_cmd_read,nice_icb_rsp_ready;wire [1:0] nice_icb_cmd_size;
  reg [31:0] ram[0:131071];integer reads,writes;
  wire [16:0] idx=(nice_icb_cmd_addr-BASE)>>2;
  assign nice_icb_cmd_ready=nice_rst_n;wire nice_icb_rsp_valid=nice_icb_cmd_valid&&nice_icb_cmd_ready;
  wire nice_icb_rsp_err=0;wire [31:0] nice_icb_rsp_rdata=ram[idx];
  kwt_nice_core #(.MEM_BASE(BASE),.MEM_BYTES(32'h80000)) dut(.*);
  always #5 nice_clk=~nice_clk;
  always @(posedge nice_clk)if(nice_icb_rsp_valid)begin
    if(!nice_icb_rsp_ready || nice_icb_cmd_size!=2)$fatal(1,"unexpected request");
    if(nice_icb_cmd_read)reads<=reads+1;
    else begin ram[idx]<=nice_icb_cmd_wdata;writes<=writes+1;end
  end
  task automatic run(input integer mode,input bit bad);
    integer i,r,g,l,y,exp,byteval,tag,total;
    reg [127:0] bits;
    begin
      for(i=0;i<131072;i=i+1)ram[i]=0;
      ram[DI]=32'h3154574b;ram[DI+1]=32'h10000+mode;ram[DI+2]=4;ram[DI+3]=BASE+4*XI;
      ram[DI+4]=BASE+4*WI;ram[DI+5]=BASE+4*BI;ram[DI+6]=BASE+4*YI;ram[DI+7]=0;
      for(i=0;i<256;i=i+1)ram[BI+i]=(128+i)<<16;
      if(mode==3)begin
        ram[XI]=198;
        for(g=0;g<32;g=g+1)ram[WI+512*g]=16;
      end
      if(bad)ram[WI]=mode==3?321:32'hf;
      total=mode==0?12672:mode==1?12896:mode==2?6752:16384;
      ram[YI-1]=32'hdeadaa55;ram[YI+total]=32'hdeadaa55;
      reads=0;writes=0;
      @(negedge nice_clk);nice_req_valid=1;@(posedge nice_clk);if(!nice_req_ready)$fatal(1,"not ready");
      @(negedge nice_clk);nice_req_valid=0;
      wait(nice_rsp_valid);@(negedge nice_clk);
      if(nice_rsp_err!==bad || nice_rsp_rdat!==(bad?1:0))$fatal(1,"status mode %d",mode);
      if(ram[YI-1]!=32'hdeadaa55||ram[YI+total]!=32'hdeadaa55)$fatal(1,"guard");
      if(bad)begin if(writes!=0)$fatal(1,"bad header wrote memory");end
      else begin
        if(reads!=(mode==3?1079:mode==2?6075:11624) || writes!=(mode==0?12672:mode==1?3456:mode==2?6752:992))$fatal(1,"transactions");
        for(r=0;r<99;r=r+1)for(g=0;g<32;g=g+1)begin
          tag=ram[YI+12672+7*g+r/16];
          if(mode==1 && ((tag>>(2*(r%16)))&3)!=(r==0?2:0))$fatal(1,"delta tag");
          for(l=0;l<8;l=l+1)begin
            y=128+8*g+l;
            case(mode)
              0:if(ram[YI+r*128+4*g+l/2][16*(l%2)+:16]!==y[15:0])$fatal(1,"raw");
              1:begin
                bits={ram[YI+r*128+4*g+3],ram[YI+r*128+4*g+2],ram[YI+r*128+4*g+1],ram[YI+r*128+4*g]};
                if(r==0 && ((bits>>(12*l))&4095)!=y)$fatal(1,"delta row 0");
                if(r!=0 && ((bits>>(4*l))&15)!=0)$fatal(1,"delta later row");
              end
              2:begin
                exp=(ram[YI+6336+13*g+r/8]>>(4*(r%8)))&15;
                if(exp!=(g<16?1:2))$fatal(1,"block exponent");
                byteval=(y+(1<<(exp-1)))>>exp;if(byteval>127)byteval=127;
                if(ram[YI+r*64+2*g+l/4][8*(l%4)+:8]!==byteval[7:0])$fatal(1,"block payload");
              end
              3:begin
                if(ram[YI+512*g]!=0)$fatal(1,"rice keys");
                if(r==0)begin
                  bits={ram[YI+512*g+2+20*l/32],ram[YI+512*g+1+20*l/32]};
                  if(((bits>>(20*l%32))&20'hfffff)!=(16*y+15))$fatal(1,"rice literal");
                end else if(ram[YI+512*g+6+(8*(r-1)+l)/32]!==0)$fatal(1,"rice zero residual");
              end
            endcase
          end
        end
      end
      nice_rsp_ready=1;@(negedge nice_clk);nice_rsp_ready=0;
    end
  endtask
  initial begin
    repeat(4)@(negedge nice_clk);nice_rst_n=1;
    run(3,1);run(0,0);run(3,0);run(2,1);run(1,0);run(2,0);run(3,0);run(0,0);
    $display("ALL PASS, 8/8 consecutive formats and recovery");$finish;
  end
  initial begin #15000000;$fatal(1,"timeout");end
endmodule

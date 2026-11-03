`timescale 1ns/1ps
// Earliest legal return: every accepted ICB command receives its response on
// the same edge. A single cold matrix deliberately exercises all four codes.
module tb_kwt_fast_return;
  localparam [31:0] BASE=32'h10000000;
  localparam X=1024,W=5120,B=13312,Y=14336;
  reg nice_clk=0,nice_rst_n=0,nice_req_valid=0,nice_rsp_ready=0;
  reg [31:0] nice_req_inst=32'h8000607b,nice_req_rs1=BASE,nice_req_rs2=0;
  wire nice_req_ready,nice_rsp_valid,nice_rsp_err,nice_active,nice_mem_holdup;
  wire [31:0] nice_rsp_rdat,nice_icb_cmd_addr,nice_icb_cmd_wdata;
  wire nice_icb_cmd_valid,nice_icb_cmd_read,nice_icb_rsp_ready;
  wire [1:0] nice_icb_cmd_size;
  wire nice_icb_cmd_ready=nice_rst_n;
  wire nice_icb_rsp_valid=nice_icb_cmd_valid && nice_icb_cmd_ready;
  wire nice_icb_rsp_err=0;
  reg [31:0] memory[0:65535],expected[0:12895];
  reg must_write[0:12895],seen[0:12895];
  wire [31:0] nice_icb_rsp_rdata=memory[(nice_icb_cmd_addr-BASE)>>2];
  integer reads=0,writes=0,expected_writes=0,r,g,l,j,n,prev,val,delta,width,tag,addr;
  reg [127:0] bits,field;
  always #5 nice_clk=~nice_clk;
  kwt_nice_core #(.MEM_BASE(BASE),.MEM_BYTES(32'h40000)) dut(.*);
  function automatic integer value(input integer row);
    integer v;begin
      case(row%5)0:v=10000;1:v=30;2:v=32;3:v=80;default:v=500;endcase
      value=((row/5)%2) ? -v : v;
    end
  endfunction
  always @(posedge nice_clk)if(nice_icb_rsp_valid)begin
    if(!nice_icb_rsp_ready || nice_icb_cmd_size!=2'd2)$fatal(1,"zero-response handshake lost");
    if(nice_icb_cmd_read)reads=reads+1;
    else begin
      addr=((nice_icb_cmd_addr-BASE)>>2)-Y;
      if(addr<0 || addr>=12896 || !must_write[addr] || seen[addr] ||
         nice_icb_cmd_wdata!==expected[addr])$fatal(1,"unexpected pin write at %d",addr);
      seen[addr]=1;writes=writes+1;
      memory[Y+addr]<=nice_icb_cmd_wdata;
    end
  end
  initial begin
    for(n=0;n<65536;n=n+1)memory[n]=0;
    for(n=0;n<12896;n=n+1)begin expected[n]=0;must_write[n]=0;seen[n]=0;end
    memory[0]=32'h3154574b;memory[1]=32'h00010001;memory[2]=0;memory[3]=BASE+4*X;
    memory[4]=BASE+4*W;memory[5]=BASE+4*B;memory[6]=BASE+4*Y;
    for(r=0;r<99;r=r+1)memory[X+r*32]=(-2*value(r)) & 16'hffff;
    for(n=0;n<128;n=n+1)memory[W+n]=32'h80008000;
    for(g=0;g<32;g=g+1)begin
      prev=0;
      for(r=0;r<99;r=r+1)begin
        val=value(r);delta=val-prev;
        tag=(delta>=-8 && delta<=7)?0:(delta>=-128 && delta<=127)?1:(delta>=-2048 && delta<=2047)?2:3;
        width=4*(tag+1);bits=0;field=(tag==3?val:delta)&((1<<width)-1);
        for(l=0;l<8;l=l+1)bits=bits|(field<<(l*width));
        for(j=0;j<=tag;j=j+1)begin n=128*r+4*g+j;must_write[n]=1;expected[n]=bits>>(32*j);end
        n=12672+7*g+r/16;must_write[n]=1;expected[n]=expected[n]|(tag<<(2*(r%16)));prev=val;
      end
    end
    for(n=0;n<12896;n=n+1)if(must_write[n])expected_writes=expected_writes+1;
    repeat(5)@(negedge nice_clk);nice_rst_n=1;
    @(negedge nice_clk);nice_req_valid=1;@(posedge nice_clk);if(!nice_req_ready)$fatal(1,"start rejected");
    @(negedge nice_clk);nice_req_valid=0;wait(nice_rsp_valid);@(negedge nice_clk);
    if(nice_rsp_err || nice_rsp_rdat!=0 || reads!=11624 || writes!=expected_writes)$fatal(1,"wrong final accounting");
    for(n=0;n<12896;n=n+1)if(seen[n]!==must_write[n])$fatal(1,"missing or extra write");
    $display("ALL PASS, 1/1 cold packed matrix with same-edge ICB, reads=%0d writes=%0d",reads,writes);$finish;
  end
  initial begin #5000000;$fatal(1,"fast response timeout");end
endmodule

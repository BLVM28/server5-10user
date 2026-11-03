`timescale 1ns/1ps
module tb_kwt_icb;
  reg clk=0;always #5 clk=~clk;
  reg rst_n=0,req_valid=0,ret_ready=0,cmd_ready=0;
  reg [31:0] req_addr=0,req_wdata=0;
  reg req_read=1,delayed_valid=0,zero_mode=0,rsp_err=0;
  wire req_ready,ret_valid,ret_err,cmd_valid,cmd_read,rsp_ready,idle;
  wire [31:0] cmd_addr,cmd_wdata,ret_rdata;wire [1:0] cmd_size;
  wire rsp_valid=zero_mode?(cmd_valid&&cmd_ready):delayed_valid;
  reg [31:0] rsp_rdata=0;
  integer t,tests=0;
  kwt_icb_master dut(.*);
  task run_case(input bit zero_response,input bit error_response,input bit read_operation);
    integer j;
    begin
      @(negedge clk);zero_mode=zero_response;rsp_err=error_response;rsp_rdata=32'h89abcdef;
      req_addr=32'h10002000;req_wdata=32'h12345678;req_read=read_operation;req_valid=1;
      @(posedge clk);if(!req_ready)$fatal(1,"master not ready");
      @(negedge clk);req_valid=0;req_addr=0;req_wdata=0;
      repeat(5)begin @(negedge clk);if(!cmd_valid||cmd_addr!==32'h10002000||
        cmd_wdata!==32'h12345678||cmd_read!==read_operation||cmd_size!==2'b10)
        $fatal(1,"command not held");end
      cmd_ready=1;@(negedge clk);cmd_ready=0;
      if(!zero_response) begin repeat(4)@(negedge clk);delayed_valid=1;
        @(negedge clk);delayed_valid=0;end
      repeat(5)begin @(negedge clk);if(!ret_valid||ret_rdata!==32'h89abcdef||ret_err!==error_response)
        $fatal(1,"response not held");end
      ret_ready=1;@(negedge clk);ret_ready=0;tests=tests+1;
    end
  endtask
  initial begin
    repeat(3)@(negedge clk);rst_n=1;
    run_case(0,0,1);run_case(1,0,0);run_case(0,1,0);run_case(1,1,1);
    $display("ALL PASS, %0d/4 ICB master checks",tests);$finish;
  end
  initial begin #20000;$fatal(1,"ICB timeout");end
endmodule

// SPDX-License-Identifier: MIT
// E203 slot for the System Bus configuration. Custom instructions report
// unsupported; all accelerator traffic is through the external System Bus.
`include "e203_defines.v"
`ifdef E203_HAS_NICE
module e203_subsys_nice_core (
  input nice_clk, nice_rst_n,
  output nice_active, nice_mem_holdup,
  input nice_req_valid, output nice_req_ready,
  input [`E203_XLEN-1:0] nice_req_inst, nice_req_rs1, nice_req_rs2,
  output nice_rsp_valid, input nice_rsp_ready,
  output [`E203_XLEN-1:0] nice_rsp_rdat, output nice_rsp_err,
  output nice_icb_cmd_valid, input nice_icb_cmd_ready,
  output [`E203_ADDR_SIZE-1:0] nice_icb_cmd_addr,
  output nice_icb_cmd_read,
  output [`E203_XLEN-1:0] nice_icb_cmd_wdata,
  output [1:0] nice_icb_cmd_size,
  input nice_icb_rsp_valid, output nice_icb_rsp_ready,
  input [`E203_XLEN-1:0] nice_icb_rsp_rdata, input nice_icb_rsp_err
);
  reg pending;
  assign nice_req_ready=nice_rst_n&&!pending;
  assign nice_rsp_valid=nice_rst_n&&pending;
  assign nice_rsp_rdat=32'h10;
  assign nice_rsp_err=pending;
  assign nice_active=pending;
  assign nice_mem_holdup=1'b0;
  assign nice_icb_cmd_valid=1'b0;
  assign nice_icb_cmd_addr=0;
  assign nice_icb_cmd_read=1'b1;
  assign nice_icb_cmd_wdata=0;
  assign nice_icb_cmd_size=2'b10;
  assign nice_icb_rsp_ready=1'b0;
  always @(posedge nice_clk or negedge nice_rst_n)
    if(!nice_rst_n) pending<=1'b0;
    else if(nice_req_valid&&nice_req_ready) pending<=1'b1;
    else if(nice_rsp_valid&&nice_rsp_ready) pending<=1'b0;
endmodule
`endif

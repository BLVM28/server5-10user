// SPDX-License-Identifier: MIT
// System Bus endpoint. SRAM and the two control words share the ordered
// reply path. The controller retires writes only after the macro edge.
module kwt_shared_sram (
    input wire clk, rst_n,
    input wire cmd_valid, cmd_read,
    output wire cmd_ready,
    input wire [31:0] cmd_addr, cmd_wdata,
    input wire [3:0] cmd_wmask,
    output wire rsp_valid, rsp_err,
    input wire rsp_ready,
    output wire [31:0] rsp_rdata,
    output wire start_valid,
    input wire start_ready,
    output reg [31:0] descriptor,
    input wire done_valid,
    input wire [31:0] done_status
);
    localparam [31:0] START_ADDR=32'ha0080000, STATUS_ADDR=32'ha0080004;
    reg busy, pending_start;
    reg [30:0] status;
    assign start_valid=pending_start;
    wire ram_address=cmd_addr[31:19]==13'h1400;
    wire start_address=cmd_addr==START_ADDR && !cmd_read && cmd_wmask==4'hf;
    wire status_address=cmd_addr==STATUS_ADDR && cmd_read;
    wire accept=cmd_valid && cmd_ready;
    wire launch=accept && start_address && !busy;
    wire bad_addr=!(ram_address || status_address || (start_address && !busy));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy <= 1'b0;
            pending_start <= 1'b0;
            status <= 0;
            descriptor <= 0;
        end else begin
            if (pending_start && start_ready) pending_start <= 1'b0;
            if (done_valid) begin
                busy <= 1'b0;
                status <= done_status[30:0];
            end
            if (launch) begin
                descriptor <= cmd_wdata;
                status <= 0;
                busy <= 1'b1;
                pending_start <= 1'b1;
            end
        end
    end

    wire ram_cs, ram_we, ram_clk, ram_response;
    wire [29:0] ram_addr;
    wire [3:0] ram_wem;
    wire [31:0] ram_din, ram_dout, ram_rdata, ctrl_response;
    kwt44_sram_icb_ctrl #(.DW(32), .MW(4), .AW(32), .AW_LSB(2),
                          .USR_W(34), .CAPACITY(4), .CLOCK_GATE(0)) u_ctrl (
        .sram_ctrl_active(), .tcm_cgstop(1'b0),
        .i_icb_cmd_valid(cmd_valid), .i_icb_cmd_ready(cmd_ready),
        .i_icb_cmd_read(cmd_read), .i_icb_cmd_addr(cmd_addr),
        .i_icb_cmd_wdata(cmd_wdata), .i_icb_cmd_wmask(cmd_wmask),
        .i_icb_cmd_usr({bad_addr,ram_address&&cmd_read,status_address?{busy,status}:32'd0}),
        .i_icb_rsp_valid(rsp_valid), .i_icb_rsp_ready(rsp_ready),
        .i_icb_rsp_rdata(ram_rdata), .i_icb_rsp_usr({rsp_err,ram_response,ctrl_response}),
        .ram_cs(ram_cs), .ram_we(ram_we), .ram_addr(ram_addr),
        .ram_wem(ram_wem), .ram_din(ram_din), .ram_dout(ram_dout),
        .clk_ram(ram_clk), .test_mode(1'b0), .clk(clk), .rst_n(rst_n)
    );
    assign rsp_rdata=ram_response?ram_rdata:ctrl_response;
    kwt_banked_sram #(.DW(32), .AW(17)) u_storage (
        .clk(ram_clk), .rst_n(rst_n), .cs(ram_cs && ram_addr[29:17]==13'h1400),
        .we(ram_we), .addr(ram_addr[16:0]), .din(ram_din),
        .wem(ram_wem), .dout(ram_dout)
    );
endmodule

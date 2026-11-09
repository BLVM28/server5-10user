`timescale 1ns/1ps
module tb_clint_pipeline;
    reg clk = 0, rst_n = 0;
    always #3.125 clk = ~clk;
    reg i_icb_cmd_valid = 0, i_icb_cmd_read = 0;
    reg [31:0] i_icb_cmd_addr = 0, i_icb_cmd_wdata = 0;
    wire i_icb_cmd_ready, i_icb_rsp_valid;
    wire [31:0] i_icb_rsp_rdata;
    wire i_icb_rsp_ready = 1'b1;
    wire io_tiles_0_mtip, io_tiles_0_msip;
    reg io_rtcToggle = 0;
    sirv_clint_top dut (.*);

    localparam [31:0] MSIP = 32'h02000000;
    localparam [31:0] CMP_LO = 32'h02004000, CMP_HI = 32'h02004004;
    localparam [31:0] TIME_LO = 32'h0200bff8, TIME_HI = 32'h0200bffc;
    bit expected_irq;
    integer compares = 0, transitions = 0;
    always @(posedge clk) if (rst_n) begin
        if ({1'b0, dut.u_sirv_clint.T_904} + 65'd1 !== dut.u_sirv_clint.T_906)
            $fatal(1, "CLINT_INCREMENT_MISMATCH");
        expected_irq = dut.u_sirv_clint.T_904 >= dut.u_sirv_clint.T_915;
        if (io_tiles_0_mtip != expected_irq) transitions = transitions + 1;
        #0.001;
        if (io_tiles_0_mtip !== expected_irq) $fatal(1, "CLINT_IRQ_LATENCY_MISMATCH");
        compares = compares + 1;
    end

    task automatic access(input bit read_cmd, input [31:0] address,
                          input [31:0] data, input [31:0] expected);
        bit received;
        reg [31:0] response;
        @(negedge clk);
        {i_icb_cmd_valid, i_icb_cmd_read, i_icb_cmd_addr, i_icb_cmd_wdata}
            = {1'b1, read_cmd, address, data};
        do @(posedge clk); while (!i_icb_cmd_ready);
        received = i_icb_rsp_valid;
        response = i_icb_rsp_rdata;
        @(negedge clk);
        i_icb_cmd_valid = 0;
        if (!received) begin
            do @(posedge clk); while (!i_icb_rsp_valid);
            response = i_icb_rsp_rdata;
        end
        if (read_cmd && response !== expected)
            $fatal(1, "CLINT_MMIO_MISMATCH addr=%h data=%h expected=%h", address, response, expected);
    endtask

    task automatic tick;
        @(negedge clk);
        io_rtcToggle = !io_rtcToggle;
        repeat (3) @(negedge clk);
    endtask

    task automatic check_irq(input bit irq);
        repeat (2) @(negedge clk);
        if (io_tiles_0_mtip !== irq) $fatal(1, "CLINT_MTIP_MISMATCH expected=%b", irq);
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1;
        check_irq(0);
        access(0, MSIP, 1, 0);
        access(1, MSIP, 0, 1);
        if (!io_tiles_0_msip) $fatal(1, "CLINT_MSIP_MISSING");
        access(0, MSIP, 0, 0);
        access(1, MSIP, 0, 0);
        if (io_tiles_0_msip) $fatal(1, "CLINT_MSIP_STUCK");

        // Cross a carry from the low 32-bit word into the high word.
        access(0, TIME_HI, 32'h0000ffff, 0);
        access(0, TIME_LO, 32'hffffffff, 0);
        access(0, CMP_HI, 32'h00010000, 0);
        access(0, CMP_LO, 0, 0);
        check_irq(0);
        tick();
        access(1, TIME_HI, 0, 32'h00010000);
        access(1, TIME_LO, 0, 0);
        check_irq(1);
        access(0, CMP_LO, 1, 0);
        check_irq(0);
        tick();
        check_irq(1);

        // A higher slice decides even when every lower slice is greater.
        access(0, CMP_HI, 32'h80000000, 0);
        access(0, CMP_LO, 0, 0);
        access(0, TIME_HI, 32'h7fffffff, 0);
        access(0, TIME_LO, 32'hffffffff, 0);
        check_irq(0);
        tick();
        check_irq(1);

        access(0, TIME_HI, 32'hffffffff, 0);
        access(0, TIME_LO, 32'hffffffff, 0);
        check_irq(1);
        tick();
        access(1, TIME_HI, 0, 0);
        access(1, TIME_LO, 0, 0);
        check_irq(0);
        if (compares < 50 || transitions < 6) $fatal(1, "CLINT_COMPARISON_COVERAGE");
        $display("CLINT_PIPELINE_PASS comparisons=%0d transitions=%0d", compares, transitions);
        $finish;
    end
    initial begin
        repeat (1000) @(posedge clk);
        $fatal(1, "CLINT_TIMEOUT");
    end
endmodule

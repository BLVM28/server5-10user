`timescale 1ns/1ps
module tb_shared_sram_pipeline;
    reg clk = 0;
    always #3.125 clk = ~clk;
    reg rst_n = 0;
    reg cmd_valid = 0, cmd_read = 0, rsp_ready = 0;
    reg [31:0] cmd_addr = 0, cmd_wdata = 0;
    reg [3:0] cmd_wmask = 0;
    reg start_ready = 0, done_valid = 0;
    reg [31:0] done_status = 0;
    wire cmd_ready, rsp_valid, rsp_err, start_valid;
    wire [31:0] rsp_rdata, descriptor;
    kwt_shared_sram dut (.*);

    localparam [31:0] BASE = 32'ha0000000, START = 32'ha0080000, STATUS = 32'ha0080004;
    reg [31:0] reference_word [0:15];
    reg [32:0] expected [0:2047];
    reg [32:0] answer, held_response;
    reg stalled = 0;
    integer issued = 0, returned = 0, longest_queue = 0, stall_cycles = 0;
    integer consecutive = 0, longest_burst = 0, accepted_starts = 0;

    always @(posedge clk) begin
        if (!rst_n) begin
            issued = 0;
            returned = 0;
            stalled = 0;
        end else begin
            if (stalled && (!rsp_valid || {rsp_err, rsp_rdata} !== held_response))
                $fatal(1, "SHARED_RESPONSE_CHANGED_UNDER_STALL");
            stalled = rsp_valid && !rsp_ready;
            if (stalled) begin
                held_response = {rsp_err, rsp_rdata};
                stall_cycles = stall_cycles + 1;
            end
            if (cmd_valid && cmd_ready) begin
                expected[issued] = answer;
                issued = issued + 1;
                consecutive = consecutive + 1;
                if (consecutive > longest_burst) longest_burst = consecutive;
            end else consecutive = 0;
            if (rsp_valid && rsp_ready) begin
                if (returned >= issued || {rsp_err, rsp_rdata} !== expected[returned])
                    $fatal(1, "SHARED_RESPONSE_MISMATCH response=%0d got=%h expected=%h",
                           returned, {rsp_err, rsp_rdata}, expected[returned]);
                returned = returned + 1;
            end
            if (issued - returned > longest_queue) longest_queue = issued - returned;
            if (start_valid && start_ready) accepted_starts = accepted_starts + 1;
        end
    end

    task automatic issue(input bit read_cmd, input [31:0] address, input [31:0] data,
                         input [3:0] mask, input [32:0] result);
        @(negedge clk);
        {cmd_valid, cmd_read, cmd_addr, cmd_wdata, cmd_wmask} = {1'b1, read_cmd, address, data, mask};
        answer = result;
        do @(posedge clk); while (!cmd_ready);
    endtask
    task automatic stop_commands;
        @(negedge clk);
        cmd_valid = 0;
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1;
        fork
            begin
                for (integer bank = 0; bank < 16; bank = bank + 1) begin
                    reference_word[bank] = 32'h10203040 + bank;
                    issue(0, BASE + bank*32768 + 32764, reference_word[bank], 4'hf, 0);
                end
                for (integer bank = 15; bank >= 0; bank = bank - 1)
                    issue(1, BASE + bank*32768 + 32767, 0, 0, {1'b0, reference_word[bank]});
                for (integer i = 0; i < 512; i = i + 1) begin
                    integer bank;
                    reg [31:0] value;
                    reg [3:0] mask;
                    bank = (i * 7) % 16;
                    value = 32'h5a789abc ^ (i * 757);
                    mask = 4'(i >> 4);
                    issue(0, BASE + bank*32768 + 32764, value, mask, 0);
                    for (integer byte_index = 0; byte_index < 4; byte_index = byte_index + 1)
                        if (mask[byte_index])
                            reference_word[bank][8*byte_index+:8] = value[8*byte_index+:8];
                    issue(1, BASE + bank*32768 + 32764, 0, 0, {1'b0, reference_word[bank]});
                end
                issue(0, START, 32'ha0000200, 4'h7, 33'h100000000);
                issue(0, START, 32'ha0000200, 4'hf, 0);
                issue(1, STATUS, 0, 0, 33'h080000000);
                issue(0, START, 32'ha0000400, 4'hf, 33'h100000000);
                issue(0, STATUS, 0, 4'hf, 33'h100000000);
                issue(1, 32'ha0080008, 0, 0, 33'h100000000);
                stop_commands();
                if (!start_valid || descriptor !== 32'ha0000200)
                    $fatal(1, "SHARED_START_CHANGED_WHILE_STALLED");
                start_ready = 1;
                @(negedge clk);
                start_ready = 0;
                done_status = 32'h0000789a;
                done_valid = 1;
                @(negedge clk);
                done_valid = 0;
                issue(1, STATUS, 0, 0, 33'h00000789a);
                stop_commands();
            end
            begin
                repeat (20) @(negedge clk);
                for (integer i = 0; i < 150; i = i + 1) begin
                    rsp_ready = 1;
                    repeat (13) @(negedge clk);
                    rsp_ready = 0;
                    repeat (5) @(negedge clk);
                end
                rsp_ready = 1;
            end
        join
        if (issued != 1063 || returned != issued || accepted_starts != 1 ||
            longest_queue != 8 || longest_burst < 8 || stall_cycles < 100)
            $fatal(1, "SHARED_COVERAGE issued=%0d returned=%0d queue=%0d burst=%0d stall=%0d starts=%0d",
                   issued, returned, longest_queue, longest_burst, stall_cycles, accepted_starts);
        $display("SHARED_STREAM_COVERAGE replies=%0d peak_outstanding=%0d burst=%0d stall_cycles=%0d",
                 returned, longest_queue, longest_burst, stall_cycles);

        rsp_ready = 0;
        issue(1, BASE + 32764, 0, 0, {1'b0, reference_word[0]});
        issue(0, START, 32'ha0000200, 4'hf, 0);
        stop_commands();
        rst_n = 0;
        repeat (3) @(negedge clk);
        if (rsp_valid || cmd_ready || start_valid) $fatal(1, "SHARED_RESET_HANDSHAKE");
        rst_n = 1;
        rsp_ready = 1;
        issue(1, STATUS, 0, 0, 0);
        stop_commands();
        repeat (6) @(negedge clk);
        if (returned != 1) $fatal(1, "SHARED_RESET_RESPONSE_COUNT");
        $display("SHARED_SRAM_PIPELINE_PASS");
        $finish;
    end
    initial begin
        repeat (5000) @(posedge clk);
        $fatal(1, "SHARED_TIMEOUT");
    end
endmodule

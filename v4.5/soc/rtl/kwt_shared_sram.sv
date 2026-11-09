// SPDX-License-Identifier: MIT
// One command can enter each cycle. SRAM data is captured locally before
// crossing banks. An ordered completion table holds early write responses
// behind older reads and absorbs arbitrary response backpressure.
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
    localparam [31:0] START_ADDR = 32'ha0080000, STATUS_ADDR = 32'ha0080004;
    localparam integer BANKS = 16, SLOTS = 8, SLOT_BITS = $clog2(SLOTS);
    reg busy, pending_start;
    reg [30:0] status;
    wire ram_address = cmd_addr[31:19] == 13'h1400;
    wire start_address = cmd_addr == START_ADDR && !cmd_read && cmd_wmask == 4'hf;
    wire status_address = cmd_addr == STATUS_ADDR && cmd_read;
    wire ram_read = ram_address && cmd_read;
    wire accept = cmd_valid && cmd_ready;
    wire launch = accept && start_address && !busy;
    wire bad_addr = !(ram_address || status_address || (start_address && !busy));

    assign start_valid = pending_start;
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

    wire [BANKS-1:0] bank_selected;
    wire [31:0] bank_data [0:BANKS-1];
    for (genvar b = 0; b < BANKS; b = b + 1) begin : bank
        assign bank_selected[b] = accept && ram_address && cmd_addr[18:15] == 4'(b);
        reg selected, write_pending;
        reg [12:0] row;
        reg [31:0] data;
        reg [3:0] mask;
        reg phase_selected, phase_write;
        reg [12:0] phase_row;
        reg [31:0] phase_data, captured_data;
        reg [3:0] phase_mask;
        wire [31:0] raw_data, wen_n;

        always @(posedge clk or negedge rst_n) begin
            if (!rst_n) selected <= 1'b0;
            else selected <= bank_selected[b];
        end
        always @(posedge clk) begin
            if (bank_selected[b]) begin
                row <= cmd_addr[14:2];
                write_pending <= !cmd_read;
                if (!cmd_read) begin
                    data <= cmd_wdata;
                    mask <= cmd_wmask;
                end
            end
            captured_data <= raw_data;
        end
        always @(negedge clk or negedge rst_n) begin
            if (!rst_n) phase_selected <= 1'b0;
            else phase_selected <= selected;
        end
        always @(negedge clk) begin
            if (selected) begin
                phase_row <= row;
                phase_write <= write_pending;
                if (write_pending) begin
                    phase_data <= data;
                    phase_mask <= mask;
                end
            end
        end
        for (genvar byte_index = 0; byte_index < 4; byte_index = byte_index + 1) begin : mask_bits
            assign wen_n[8*byte_index +: 8] = {8{~phase_mask[byte_index]}};
        end
        RAMSP8KX32 ram (
            .CLK(clk), .CEN(~phase_selected), .GWEN(~phase_write), .WEN(wen_n),
            .A(phase_row), .D(phase_data), .Q(raw_data),
            .EMA(3'd2), .EMAW(2'd0), .RET1N(1'b1)
        );
        assign bank_data[b] = captured_data;
    end

    reg [SLOT_BITS-1:0] head, tail, slot_issue, slot_sram, slot_data;
    reg [SLOT_BITS:0] used;
    reg [SLOTS-1:0] complete, error_slots;
    reg [31:0] data_slots [0:SLOTS-1];
    reg early_reply, read_sram, read_data;
    reg [BANKS-1:0] read_bank_issue, read_bank_sram, read_bank_data;
    reg [31:0] selected_data;

    always @* begin
        selected_data = 32'd0;
        for (integer i = 0; i < BANKS; i = i + 1)
            selected_data = selected_data | (bank_data[i] & {32{read_bank_data[i]}});
    end

    assign cmd_ready = rst_n && used < (SLOT_BITS+1)'(SLOTS);
    assign rsp_valid = rst_n && used != 0 && complete[head];
    assign rsp_err = error_slots[head];
    assign rsp_rdata = data_slots[head];
    wire retire = rsp_valid && rsp_ready;

    // Relative to command acceptance, the macro executes at +1, the bank
    // data is captured at +2, and the read slot completes at +3. Writes
    // and MMIO complete at +1. All responses retire in acceptance order.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            head <= 0;
            tail <= 0;
            used <= 0;
            complete <= 0;
            early_reply <= 1'b0;
            read_sram <= 1'b0;
            read_data <= 1'b0;
            read_bank_issue <= 0;
        end else begin
            early_reply <= accept && !ram_read;
            read_bank_issue <= ram_read ? bank_selected : {BANKS{1'b0}};
            read_sram <= |read_bank_issue;
            read_data <= read_sram;

            if (accept) begin
                complete[tail] <= 1'b0;
                tail <= tail + 1'b1;
            end
            if (retire) head <= head + 1'b1;
            if (early_reply) complete[slot_issue] <= 1'b1;
            if (read_data) complete[slot_data] <= 1'b1;
            case ({accept, retire})
                2'b10: used <= used + 1'b1;
                2'b01: used <= used - 1'b1;
                default: ;
            endcase
        end
    end
    always @(posedge clk) begin
        if (accept) begin
            slot_issue <= tail;
            error_slots[tail] <= bad_addr;
            if (!ram_read) data_slots[tail] <= status_address ? {busy, status} : 32'd0;
        end
        slot_sram <= slot_issue;
        slot_data <= slot_sram;
        read_bank_sram <= read_bank_issue;
        read_bank_data <= read_bank_sram;
        if (read_data) data_slots[slot_data] <= selected_data;
    end
endmodule

// SPDX-License-Identifier: MIT
// Ordered synchronous SRAM channel with registered ingress and egress.
// Request phase capture uses the parent clock, even if the RAM clock is gated.
module kwt44_sram_icb_ctrl #(
    parameter integer DW=32, MW=4, AW=32, AW_LSB=2, USR_W=1,
    parameter integer CAPACITY=3, CLOCK_GATE=0, HOLD_LAST_RESPONSE=0
)(
    output wire sram_ctrl_active,
    input wire tcm_cgstop,
    input wire i_icb_cmd_valid,
    output wire i_icb_cmd_ready,
    input wire i_icb_cmd_read,
    input wire [AW-1:0] i_icb_cmd_addr,
    input wire [DW-1:0] i_icb_cmd_wdata,
    input wire [MW-1:0] i_icb_cmd_wmask,
    input wire [USR_W-1:0] i_icb_cmd_usr,
    output wire i_icb_rsp_valid,
    input wire i_icb_rsp_ready,
    output wire [DW-1:0] i_icb_rsp_rdata,
    output wire [USR_W-1:0] i_icb_rsp_usr,
    output reg ram_cs, ram_we,
    output reg [AW-AW_LSB-1:0] ram_addr,
    output reg [MW-1:0] ram_wem,
    output reg [DW-1:0] ram_din,
    input wire [DW-1:0] ram_dout,
    output wire clk_ram,
    input wire test_mode, clk, rst_n
);
    localparam integer CMD_WIDTH=1+(AW-AW_LSB)+DW+MW+USR_W;
    localparam [2:0] MAX_USED=3'(CAPACITY);
    reg [2:0] used;
    wire credit=used < MAX_USED;
    wire command_room, command_valid, read_command;
    wire [AW-AW_LSB-1:0] address_command;
    wire [DW-1:0] data_command;
    wire [MW-1:0] mask_command;
    wire [USR_W-1:0] user_command;
    reg [USR_W-1:0] phase_user, memory_user;
    reg memory_valid;
    wire accepted=i_icb_cmd_valid && i_icb_cmd_ready;
    wire retired=i_icb_rsp_valid && i_icb_rsp_ready;
    wire response_room;
    wire [DW-1:0] response_data;

    assign i_icb_cmd_ready=credit && command_room;
    assign sram_ctrl_active=i_icb_cmd_valid || used!=0;

    kwt44_fifo #(.WIDTH(CMD_WIDTH), .DEPTH(2)) command_queue (
        .clk(clk), .rst_n(rst_n),
        .push_valid(i_icb_cmd_valid && credit), .push_ready(command_room),
        .push_data({i_icb_cmd_read,i_icb_cmd_addr[AW-1:AW_LSB],
                    i_icb_cmd_wdata,i_icb_cmd_wmask,i_icb_cmd_usr}),
        .pop_valid(command_valid), .pop_ready(ram_cs),
        .pop_data({read_command,address_command,data_command,mask_command,user_command})
    );

    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ram_cs <= 1'b0;
            ram_we <= 1'b0;
        end else begin
            ram_cs <= command_valid;
            ram_we <= command_valid && !read_command;
        end
    end
    always @(negedge clk) begin
        if (command_valid) begin
            ram_addr <= address_command;
            ram_wem <= mask_command;
            ram_din <= data_command;
            phase_user <= user_command;
        end
    end
    generate if (CLOCK_GATE) begin: gated
        e203_clkgate gate_ram (
            .clk_in(clk), .test_mode(test_mode),
            .clock_en(ram_cs || tcm_cgstop), .clk_out(clk_ram)
        );
    end else begin: ungated
        assign clk_ram=clk;
    end endgenerate

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            memory_valid <= 1'b0;
            used <= 0;
        end else begin
            memory_valid <= ram_cs;
            case ({accepted,retired})
                2'b10: used <= used+1'b1;
                2'b01: used <= used-1'b1;
                default: ;
            endcase
        end
    end
    always @(posedge clk)
        if (ram_cs) memory_user <= phase_user;

    // The credit is reserved at command acceptance. All launched requests
    // can therefore retire to this queue, even when the consumer is stalled.
    kwt44_fifo #(.WIDTH(DW+USR_W), .DEPTH(4)) response_queue (
        .clk(clk), .rst_n(rst_n),
        .push_valid(memory_valid), .push_ready(response_room),
        .push_data({memory_user,ram_dout}),
        .pop_valid(i_icb_rsp_valid), .pop_ready(i_icb_rsp_ready),
        .pop_data({i_icb_rsp_usr,response_data})
    );
    generate if (HOLD_LAST_RESPONSE) begin: keep_ifetch_data
        // The E203 IFU may reuse the most recently delivered ITCM word
        // when the outer controller asserts its holdup indication.
        reg [DW-1:0] last_data;
        always @(posedge clk)
            if (retired) last_data <= response_data;
        assign i_icb_rsp_rdata=i_icb_rsp_valid?response_data:last_data;
    end else begin: ordinary_response
        assign i_icb_rsp_rdata=response_data;
    end endgenerate
    generate if (CAPACITY<2 || CAPACITY>4) begin: invalid_capacity
        KWT44_INVALID_SRAM_CAPACITY invalid();
    end endgenerate
`ifndef SYNTHESIS
    always @(posedge clk)
        if (rst_n && memory_valid && !response_room) $fatal(1,"KWT44_SRAM_RESPONSE_OVERFLOW");
`endif
endmodule

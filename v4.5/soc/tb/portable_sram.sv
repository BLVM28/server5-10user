// SPDX-License-Identifier: MIT
// Local simulation only. Read and byte/bit-mask behavior matches the tested
// macro interface. This file has no technology timing or electrical model.
module kwt44_sim_platform_ram #(parameter integer AW=13,DW=32)(
    input wire CLK,CEN,GWEN,
    input wire [DW-1:0] WEN,D,
    input wire [AW-1:0] A,
    output reg [DW-1:0] Q
);
    reg [DW-1:0] mem[0:(1<<AW)-1];
    always @(posedge CLK) if(!CEN) begin
        if(GWEN) Q<=mem[A];
        else for(integer bit_index=0;bit_index<DW;bit_index=bit_index+1)
            if(!WEN[bit_index]) mem[A][bit_index]<=D[bit_index];
    end
endmodule

module RAMSP8KX32(
    input wire CLK,CEN,GWEN,RET1N,
    input wire [31:0] WEN,D,
    input wire [12:0] A,
    input wire [2:0] EMA,
    input wire [1:0] EMAW,
    output wire [31:0] Q
);
    kwt44_sim_platform_ram ram(.CLK(CLK),.CEN(CEN),.GWEN(GWEN),.WEN(WEN),.A(A),.D(D),.Q(Q));
endmodule

module RAMSP4KX64(
    input wire CLK,CEN,GWEN,RET1N,
    input wire [63:0] WEN,D,
    input wire [11:0] A,
    input wire [2:0] EMA,
    input wire [1:0] EMAW,
    output wire [63:0] Q
);
    kwt44_sim_platform_ram #(.AW(12),.DW(64)) ram(
        .CLK(CLK),.CEN(CEN),.GWEN(GWEN),.WEN(WEN),.A(A),.D(D),.Q(Q));
endmodule

module CLKLANAQV4_12TH40(input wire CK,E,TE,output wire Q);
    reg enabled=0;
    always @* if(!CK) enabled=E||TE;
    assign Q=CK&&enabled;
endmodule
module CLKMUX2V4_12TH40(input wire I0,I1,S,output wire Z);
    assign Z=S?I1:I0;
endmodule

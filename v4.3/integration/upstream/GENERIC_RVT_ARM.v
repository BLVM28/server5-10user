`ifndef FPGA
module GENERIC_BUF_RVT (Y, A);
    output Y;
    input  A;
    `ifdef FPGA
        assign Y = A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        BUFCARMX9 u_donttouch_BUF(.O(Y),.I(A));
    `endif
endmodule

module GENERIC_CLKBUF_RVT (Y, A);
    output Y;
    input  A;
    `ifdef FPGA
        assign Y = A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        BUFCKCARMX4 u_donttouch_CLKBUF(.O(Y),.I(A));
    `endif
endmodule

module GENERIC_CLKAND2_RVT (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = A & B;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        AN2CKCARMX3 u_donttouch_CLKAND2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_CLKNAND2_RVT (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = !(A & B);
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        ND2CKCARMX1 u_donttouch_CLKNAND2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_CLKMX2_RVT (Y, S0, A, B);
    input  A, B, S0;
    output Y;
    `ifdef FPGA
        assign Y = S0 ? B : A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        MUX2CKCARMX4 u_donttouch_CLKMX2(.O(Y),.S(S0),.A(A),.B(B));
    `endif
endmodule

module GENERIC_CLKINV_RVT (Y, A);
    output Y;
    input  A;
    `ifdef FPGA
        assign Y = !A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        INVCKCARMX4 u_donttouch_CLKINV(.O(Y),.I(A));
    `endif
endmodule

module GENERIC_CLKOR2_RVT (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = A | B;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        OR2CKCARMX3 u_donttouch_CLKOR2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_SEDFF_RVT (D,  CK , E , Q);
    output Q;
    input  D, CK, E;
    `ifdef FPGA
        reg Q;
        always @ (posedge CK) begin
            if(E) begin
                Q <= #0.1 (D === 1'bz) ? 1'bx : D;
            end
        end
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        wire EB;
        INVCARMX4 u_donttouch_inv(.O(EB), .I(E));
        QDFZENCARMX2 u_donttouch_SEDFF_QDFEN(.Q(Q),.D(D),.TD(1'b0),.CK(CK),.SEL(1'b0),.EB(EB));
    `endif
endmodule

module GENERIC_SDFFR_RVT(Q, D, CK, RN);
    output Q;
    input D, CK, RN;
    `ifdef FPGA
        reg Q;
        always @ (posedge CK or negedge RN) begin
            if(!RN) begin
                Q <= 1'b0;
            end
            else begin
                Q <= D;
            end
        end
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        QDFZRBNCARMX2 u_donttouch_SDFFR(.Q(Q), .D(D), .TD(1'b0), .CK(CK), .SEL(1'b0), .RB(RN));
    `endif
endmodule

module GENERIC_CLOCKGATE_RVT (ECK, E, SE, CK);
    output ECK;
    input E, SE, CK;
    `ifdef FPGA
        reg latch_out;
        always @ (CK or E or SE) begin
            if(!CK) begin
                latch_out = E | SE;
            end
        end
        assign ECK = latch_out & CK;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        GCKESCARMX4 u_donttouch_CLOCKGATE(.Q(ECK), .E(E), .TE(SE), .CK(CK));
    `endif
endmodule

module GENERIC_CLKXOR2_RVT (Y, A0, A1);
    output Y;
    input  A0, A1;
    `ifdef FPGA
        assign Y = A0 ^ A1;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        XOR2CKCARMX3 u_donttouch_CLKXOR2(.O(Y),.I1(A0),.I2(A1));
    `endif
endmodule

module GENERIC_INV_RVT (Y, A);
    output Y;
    input  A;
    `ifdef FPGA
        assign Y = !A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        INVCARMX9 u_donttouch_INV(.O(Y),.I(A));
    `endif
endmodule

module GENERIC_NAND2_RVT (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = !(A & B);
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        ND2CARMX3 u_donttouch_NAND2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_NOR2_RVT (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = !(A | B);
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        NR2CARMX3 u_donttouch_NOR2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_OR2_RVT (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = A | B;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        OR2CARMX2 u_donttouch_OR2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_CLKMX8_RVT(Y, S0, S1, S2, A, B, C, D, E, F, G, H);
    input  S0, S1, S2, A, B, C, D, E, F, G, H;
    output Y;
    `ifdef FPGA
        reg Y_reg;
        assign Y = Y_reg;
        always @ (*) begin
            Y_reg = 1'b0;
            case({S2,S1,S0})
                3'b000 : Y_reg = A;
                3'b001 : Y_reg = B;
                3'b010 : Y_reg = C;
                3'b011 : Y_reg = D;
                3'b100 : Y_reg = E;
                3'b101 : Y_reg = F;
                3'b110 : Y_reg = G;
                3'b111 : Y_reg = H;
            endcase
        end
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        wire O1_1, O1_2, O1_3, O1_4;
        MUX2CKCARMX4  u_donttouch_CLKMX2_1 (.O(O1_1), .S(S0), .A(A), .B(B));
        MUX2CKCARMX4  u_donttouch_CLKMX2_2 (.O(O1_2), .S(S0), .A(C), .B(D));
        MUX2CKCARMX4  u_donttouch_CLKMX2_3 (.O(O1_3), .S(S0), .A(E), .B(F));
        MUX2CKCARMX4  u_donttouch_CLKMX2_4 (.O(O1_4), .S(S0), .A(G), .B(H));
        wire O2_1, O2_2;                   
        MUX2CKCARMX4  u_donttouch_CLKMX2_5 (.O(O2_1), .S(S1), .A(O1_1), .B(O1_2));
        MUX2CKCARMX4  u_donttouch_CLKMX2_6 (.O(O2_2), .S(S1), .A(O1_3), .B(O1_4));
        MUX2CKCARMX4  u_donttouch_CLKMX2_7 (.O(Y), .S(S2), .A(O2_1), .B(O2_2));
    `endif
endmodule

module GENERIC_CLKMX4_RVT(Y, S0, S1, A, B, C, D);
    input  S0, S1, A, B, C, D;
    output Y;
    `ifdef FPGA
        assign Y = S1 ? 
                   (S0 ? D : C) :
                   (S0 ? B : A) ;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        wire O1, O2;
        MUX2CKCARMX4  u_donttouch_CLKMX2_1 (.O(O1), .S(S0), .A(A), .B(B));
        MUX2CKCARMX4  u_donttouch_CLKMX2_2 (.O(O2), .S(S0), .A(C), .B(D));
        MUX2CKCARMX4  u_donttouch_CLKMX2_3 (.O(Y), .S(S1), .A(O1), .B(O2));
    `endif
endmodule

module GENERIC_DFFRD2_RVT ( Q,QN, D, CK,RN);
    output Q, QN;
    input D, CK, RN;
    `ifdef FPGA
        reg Q;
        always @ (posedge CK or negedge RN) begin
            if(!RB) begin
                Q <= 1'b0;
            end
            else begin
                Q <= D;
            end
        end
        assign QN = !Q;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        QDFFRBNCARMX2 u_donttouch_QDFFRB(.Q(Q), .D(D), .CK(CK), .RB(RN));
        INVCKCARMX4 u_donttouch_CLKINV(.O(QN),.I(Q));
    `endif
endmodule

module GENERIC_BUF_RVT_12T (Y, A);
    output Y;
    input  A;
    `ifdef FPGA
        assign Y = A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        BUFCGRMX9 u_donttouch_BUF(.O(Y),.I(A));
    `endif
endmodule

module GENERIC_CLKBUF_RVT_12T (Y, A);
    output Y;
    input  A;
    `ifdef FPGA
        assign Y = A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        BUFCKCGRMX4 u_donttouch_CLKBUF(.O(Y),.I(A));
    `endif
endmodule

module GENERIC_CLKAND2_RVT_12T (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = A & B;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        AN2CKCGRMX3 u_donttouch_CLKAND2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_CLKNAND2_RVT_12T (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = !(A & B);
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        ND2CKCGRMX3 u_donttouch_CLKNAND2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_CLKMX2_RVT_12T (Y, S0, A, B);
    input  A, B, S0;
    output Y;
    `ifdef FPGA
        assign Y = S0 ? B : A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        MUX2CKCGRMX4 u_donttouch_CLKMX2(.O(Y),.S(S0),.A(A),.B(B));
    `endif
endmodule

module GENERIC_CLKINV_RVT_12T (Y, A);
    output Y;
    input  A;
    `ifdef FPGA
        assign Y = !A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        INVCKCGRMX4 u_donttouch_CLKINV(.O(Y),.I(A));
    `endif
endmodule

module GENERIC_CLKOR2_RVT_12T (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = A | B;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        OR2CKCGRMX3 u_donttouch_CLKOR2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_SEDFF_RVT_12T (D,  CK , E , Q);
    output Q;
    input  D, CK, E;
    `ifdef FPGA
        reg Q;
        always @ (posedge CK) begin
            if(E) begin
                Q <= #0.1 (D === 1'bz) ? 1'bx : D;
            end
        end
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        wire EB;
        INVCGRMX4 u_donttouch_inv(.O(EB), .I(E));
        QDFZENCGRMX2 u_donttouch_SEDFF_QDFEN(.Q(Q),.D(D),.TD(1'b0),.CK(CK),.SEL(1'b0),.EB(EB));
    `endif
endmodule

module GENERIC_SDFFR_RVT_12T(Q, D, CK, RN);
    output Q;
    input D, CK, RN;
    `ifdef FPGA
        reg Q;
        always @ (posedge CK or negedge RN) begin
            if(!RN) begin
                Q <= 1'b0;
            end
            else begin
                Q <= D;
            end
        end
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        QDFZRBNCGRMX2 u_donttouch_SDFFR(.Q(Q), .D(D), .TD(1'b0), .CK(CK), .SEL(1'b0), .RB(RN));
    `endif
endmodule

module GENERIC_CLOCKGATE_RVT_12T (ECK, E, SE, CK);
    output ECK;
    input E, SE, CK;
    `ifdef FPGA
        reg latch_out;
        always @ (CK or E or SE) begin
            if(!CK) begin
                latch_out = E | SE;
            end
        end
        assign ECK = latch_out & CK;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        GCKESCGRMX4 u_donttouch_CLOCKGATE(.Q(ECK), .E(E), .TE(SE), .CK(CK));
    `endif
endmodule

module GENERIC_CLKXOR2_RVT_12T (Y, A0, A1);
    output Y;
    input  A0, A1;
    `ifdef FPGA
        assign Y = A0 ^ A1;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        XOR2CKCGRMX3 u_donttouch_CLKXOR2(.O(Y),.I1(A0),.I2(A1));
    `endif
endmodule

module GENERIC_INV_RVT_12T (Y, A);
    output Y;
    input  A;
    `ifdef FPGA
        assign Y = !A;
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        INVCGRMX9 u_donttouch_INV(.O(Y),.I(A));
    `endif
endmodule

module GENERIC_NAND2_RVT_12T (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = !(A & B);
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        ND2CGRMX3 u_donttouch_NAND2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule

module GENERIC_NOR2_RVT_12T (Y, A, B);
    output Y;
    input  A, B;
    `ifdef FPGA
        assign Y = !(A | B);
    `else
// synopsys dc_script_begin
// set_dont_touch u_donttouch_*
// synopsys dc_script_end
        NR2CGRMX3 u_donttouch_NOR2(.O(Y),.I1(A),.I2(B));
    `endif
endmodule
`endif

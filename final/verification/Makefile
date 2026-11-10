RTL ?= $(CURDIR)/..
BUILD ?= $(CURDIR)/build
JOBS ?= 4
TB := $(CURDIR)/tb
VECTORS := $(CURDIR)/vec/worst

.PHONY: check units matrix model
check: units matrix

units:
	mkdir -p "$(BUILD)"
	iverilog -g2012 -s tb_icb_registered -o "$(BUILD)/icb" "$(RTL)/rtl/kwt43_icb_master.sv" "$(TB)/tb_icb_registered.sv"
	vvp "$(BUILD)/icb" > "$(BUILD)/icb.log"
	grep -F 'ICB_REGISTERED_PASS completed=2000 aborted=2 zero=1000 delayed=1001' "$(BUILD)/icb.log"
	iverilog -g2012 -s tb_mul16_pipeline -o "$(BUILD)/multiply" "$(RTL)/rtl/kwt_mul16_pipe.sv" "$(TB)/tb_mul16_pipeline.sv"
	vvp "$(BUILD)/multiply" > "$(BUILD)/multiply.log"
	grep -F 'MULTIPLY_PIPELINE_PASS checked=16449 aborted=2' "$(BUILD)/multiply.log"
	iverilog -g2012 -s tb_kwt_stream_dot -o "$(BUILD)/dot" "$(RTL)/rtl/kwt_mul16_pipe.sv" "$(RTL)/rtl/kwt43_dot.sv" "$(RTL)/rtl/kwt_quantize.sv" "$(TB)/tb_kwt_stream_dot.sv"
	vvp "$(BUILD)/dot" > "$(BUILD)/dot.log"
	grep -F 'ALL PASS, 64/64' "$(BUILD)/dot.log"

matrix:
	mkdir -p "$(BUILD)"
	cd "$(RTL)" && verilator --binary --timing -j $(JOBS) -Wno-fatal --top-module tb_kwt_streams -DKWT_PERIOD_NS=6.25 --Mdir "$(BUILD)/matrix" -f rtl.f "$(TB)/kwt_sram_sim.sv" "$(TB)/tb_kwt_streams.sv" > "$(BUILD)/matrix_compile.log" 2>&1
	"$(BUILD)/matrix/Vtb_kwt_streams" "+VEC_DIR=$(VECTORS)" > "$(BUILD)/matrix.log" 2>&1
	grep -F 'STREAM GUARD PASS 25/25' "$(BUILD)/matrix.log"
	grep -F 'ALL PASS, 29/29 NICE/matrix scenarios' "$(BUILD)/matrix.log"

model:
	python3 -B "$(CURDIR)/../model/verify_frozen.py"

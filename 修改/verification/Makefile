RTL ?= $(CURDIR)/..
BUILD ?= $(CURDIR)/build
JOBS ?= 4
PYTHON ?= python3
TB := $(CURDIR)/tb
VECTORS := $(CURDIR)/vec/worst
BUS_MODE ?= 0
PACK ?= 1
PERIOD ?= 6.666667
MATRIX_BUILD := $(BUILD)/matrix_b$(BUS_MODE)_p$(PACK)
MATRIX_LOG := $(BUILD)/matrix_b$(BUS_MODE)_p$(PACK).log
PACK_FLAG := $(if $(filter 0,$(PACK)),-DKWT_TEST_SWAP,)

.PHONY: check units writer codec matrix compile run model clean stress help
check: units writer codec model matrix

help:
	@echo 'make check          component + writer + numerical model + 12-layer RTL regression'
	@echo 'make compile/run    compile or run matrix RTL (default BUS_MODE=0 PACK=1)'
	@echo 'make stress         immediate + random-wait/swapped-word bus regression'
	@echo 'make clean          delete only this verification/build directory'
	@echo 'RTL simulation proves logic; it does not prove 150/160 MHz STA or SoC compliance.'

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

writer:
	mkdir -p "$(BUILD)"
	iverilog -g2012 -s tb_raw_writer -o "$(BUILD)/writer" "$(RTL)/rtl/kwt43_writer.sv" "$(TB)/tb_raw_writer.sv"
	vvp "$(BUILD)/writer" > "$(BUILD)/writer.log"
	grep -F 'RAW_WRITER_PASS numeric_cases=393216 groups=6 words=4752' "$(BUILD)/writer.log"

codec:
	mkdir -p "$(BUILD)"
	gcc -std=c11 -Wall -Wextra -fsanitize=undefined -I"$(RTL)/interface" "$(CURDIR)/test_codec.c" -o "$(BUILD)/codec"
	"$(BUILD)/codec" "$(CURDIR)/vec" > "$(BUILD)/codec.log"
	grep -F 'C_CODEC_PASS layers=12 pack_modes=2 raw_y_values=608256' "$(BUILD)/codec.log"

compile:
	mkdir -p "$(BUILD)"
	cd "$(RTL)" && verilator --binary --timing -j $(JOBS) -Wno-fatal --top-module tb_kwt_streams -GBUS_MODE=$(BUS_MODE) $(PACK_FLAG) -DKWT_PERIOD_NS=$(PERIOD) --Mdir "$(MATRIX_BUILD)" -f rtl.f "$(TB)/kwt_sram_sim.sv" "$(TB)/tb_kwt_streams.sv" > "$(BUILD)/compile_b$(BUS_MODE)_p$(PACK).log" 2>&1

run: compile
	"$(MATRIX_BUILD)/Vtb_kwt_streams" "+VEC_DIR=$(VECTORS)" > "$(MATRIX_LOG)" 2>&1
	grep -F 'STREAM GUARD PASS 26/26' "$(MATRIX_LOG)"
	grep -F 'ALL PASS, 29/29 NICE/matrix scenarios' "$(MATRIX_LOG)"
	mkdir -p "$(CURDIR)/../reports/logs"
	cp "$(MATRIX_LOG)" "$(CURDIR)/../reports/logs/"

matrix: run

stress:
	$(MAKE) matrix BUS_MODE=2 PACK=1
	$(MAKE) matrix BUS_MODE=1 PACK=0

model:
	cd "$(CURDIR)/../model" && $(PYTHON) -B verify_frozen.py

clean:
	python3 -c 'from pathlib import Path; import shutil; p=Path("$(BUILD)").resolve(); expected=Path("$(CURDIR)/build").resolve(); assert p==expected, "clean only supports default build path"; shutil.rmtree(p) if p.exists() else None'

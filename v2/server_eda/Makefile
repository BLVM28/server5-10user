PYTHON ?= python3
LIB_CONFIG ?= ../../library_selection.json
PERIOD ?= 6.666667
TAG ?= v2_reset
RAW_TAG ?= v2_150
HOLD_FIX ?= 1
RTL_ROOT ?= ..
BASELINE ?= /storage2/2026contest/server5/s5_10usr/kwt_eda_tmp_20261101/project
ARGS = --period $(PERIOD) --tag $(TAG) --hold-fix $(HOLD_FIX) --rtl-root $(abspath $(RTL_ROOT))
.NOTPARALLEL:
.PHONY: all functional activation overlap pipeline binding benchmark sram150 dot150 synth repair sta gate fullgate summary
all: functional activation overlap pipeline binding sram150 dot150 synth repair sta gate fullgate benchmark summary
overlap:
	$(PYTHON) run_checks.py overlap $(ARGS)
binding:
	$(PYTHON) binding.py
pipeline:
	$(PYTHON) run_checks.py pipeline $(ARGS)
benchmark:
	$(PYTHON) benchmark.py --baseline $(BASELINE)
functional:
	$(PYTHON) run_checks.py functional $(ARGS)
activation:
	$(PYTHON) run_checks.py activation $(ARGS)
sram150:
	$(PYTHON) run_checks.py sram150 $(ARGS)
dot150:
	$(PYTHON) run_checks.py dot150 $(ARGS)
synth:
	$(PYTHON) run_checks.py synth --libraries $(LIB_CONFIG) $(ARGS) --tag $(RAW_TAG)
repair:
	$(PYTHON) repair_reset.py --source $(RAW_TAG) --tag $(TAG) --period $(PERIOD)
sta:
	$(PYTHON) run_checks.py sta --libraries $(LIB_CONFIG) $(ARGS)
gate:
	$(PYTHON) run_checks.py gate --libraries $(LIB_CONFIG) $(ARGS)
fullgate:
	$(PYTHON) full_gate.py --tag $(TAG)
summary:
	$(PYTHON) run_checks.py summary $(ARGS)

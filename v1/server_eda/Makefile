PYTHON ?= python3
LIB_CONFIG ?= ../../library_selection.json
.NOTPARALLEL:
.PHONY: all functional activation sram150 dot150 synth sta gate summary
all: functional activation sram150 dot150 synth sta gate summary
functional:
	$(PYTHON) run_checks.py functional
activation:
	$(PYTHON) run_checks.py activation
sram150:
	$(PYTHON) run_checks.py sram150
dot150:
	$(PYTHON) run_checks.py dot150
synth:
	$(PYTHON) run_checks.py synth --libraries $(LIB_CONFIG)
sta:
	$(PYTHON) run_checks.py sta --libraries $(LIB_CONFIG)
gate:
	$(PYTHON) run_checks.py gate --libraries $(LIB_CONFIG)
summary:
	$(PYTHON) run_checks.py summary

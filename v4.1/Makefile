SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
PERIOD ?= 6.666667
JOBS ?= 2
DAILY := env clean compile run regress paired waves verdi negative timing sweep report synth vectors package
.PHONY: help $(DAILY) sta check acceptance gate_sample immediate modes
help:
	@echo 'make check / paired / acceptance  = base+timing / measured throughput / release evidence'
	@echo 'make clean / compile / run / regress JOBS=2 / waves / verdi / timing PERIOD=6.666667 / sweep'
	@echo 'make vectors / package / immediate / gate_sample'
$(DAILY):
	$(PYTHON) -B server_eda/daily.py $@ --period "$(PERIOD)" --jobs "$(JOBS)"
sta: timing
check: env run timing report
acceptance:
	$(PYTHON) -B server_eda/evidence.py acceptance
gate_sample:
	$(PYTHON) -B server_eda/gate_sample.py --period "$(PERIOD)"
immediate:
	$(PYTHON) -B server_eda/immediate.py
modes:
	$(PYTHON) -B server_eda/modes.py

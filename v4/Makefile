SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
PERIOD ?= 6.666667
NETLIST ?= rebuilt
VEC ?= $(CURDIR)/vec
JOBS ?= 4
TARGETS := env clean compile run negative regress timing sweep report synth waves verdi probe gate paired package vectors
ARGS = --period "$(PERIOD)" --netlist "$(NETLIST)" --vec "$(VEC)" --jobs "$(JOBS)"
.PHONY: help $(TARGETS) check sta acceptance gate_sample fast_return
help:
	@echo 'v4 / NICE accelerator / contest 150 MHz'
	@echo 'make check   = env + 9 functional suites + SS/FF STA + report'
	@echo 'make clean | compile | run | negative | regress | timing | report'
	@echo 'make timing PERIOD=6.666667  : contest 150 MHz'
	@echo 'make sweep   : fixed netlist at 150 / 160 / 180 / 200 MHz'
	@echo 'make waves; make verdi       : generate VCD, then view'
	@echo 'make paired  : 12 cold tasks for raw and packed formats, NICE cycles and tasks/s at 150 MHz'
	@echo 'make vectors | package : verify data / rebuild five verified ZIPs'
	@echo 'make synth; make timing : qualify modified RTL'
	@echo 'make timing; make probe      : optional SDF annotation test'
	@echo 'make gate_sample : complete packed matrix at SS and FF with SDF'
	@echo 'make fast_return : complete matrix with all ICB responses on command acceptance'
	@echo 'make acceptance  : verify retained regression, SDF and class throughput receipts'
	@echo 'make gate JOBS=4             : optional long 12-layer gate, same PERIOD/NETLIST as timing'
$(TARGETS):
	$(PYTHON) server_eda/daily.py $@ $(ARGS)
sta: timing
check: env run timing report
gate_sample:
	$(PYTHON) -B server_eda/gate_sample.py --period "$(PERIOD)"
fast_return:
	$(PYTHON) -B server_eda/fast_return.py
acceptance:
	$(PYTHON) -B server_eda/evidence.py acceptance

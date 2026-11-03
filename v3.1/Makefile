SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
PERIOD ?= 5.0
NETLIST ?= rebuilt
VEC ?= $(CURDIR)/vec
JOBS ?= 4
TARGETS := env clean compile run negative regress timing sweep report synth waves verdi probe gate paired package vectors
ARGS = --period "$(PERIOD)" --netlist "$(NETLIST)" --vec "$(VEC)" --jobs "$(JOBS)"
.PHONY: help $(TARGETS) check sta acceptance
help:
	@echo 'v3.1 / full NICE accelerator / default 200 MHz'
	@echo 'make check   = env + 7 functional suites + SS/FF STA + report'
	@echo 'make clean | compile | run | negative | regress | timing | report'
	@echo 'make timing PERIOD=6.666667  : contest 150 MHz'
	@echo 'make sweep   : fixed netlist at 150 / 180 / 200 / 210 / 215 / 220 MHz'
	@echo 'make waves; make verdi       : generate VCD, then view'
	@echo 'make paired  : 12 worst tasks, total cycles and same-clock throughput gain over v3'
	@echo 'make vectors | package : verify data / rebuild five verified ZIPs'
	@echo 'make synth; make timing : qualify modified RTL'
	@echo 'make timing; make probe      : optional SDF annotation test'
	@echo 'make gate JOBS=4             : optional long 12-layer gate, same PERIOD/NETLIST as timing'
$(TARGETS):
	$(PYTHON) server_eda/daily.py $@ $(ARGS)
sta: timing
check: env run timing report
acceptance:
	$(PYTHON) -B server_eda/evidence.py acceptance

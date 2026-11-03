SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
PERIOD ?= 5.0
NETLIST ?= qualified200
VEC ?= $(CURDIR)/vec
JOBS ?= 4
TARGETS := env clean compile run negative regress timing sweep report synth waves verdi probe gate package vectors
ARGS = --period "$(PERIOD)" --netlist "$(NETLIST)" --vec "$(VEC)" --jobs "$(JOBS)"
.PHONY: help $(TARGETS) check sta
help:
	@echo 'v3 / full NICE accelerator / default 200 MHz'
	@echo 'make check   = env + 7 functional suites + SS/FF STA + report'
	@echo 'make clean | compile | run | negative | regress | timing | report'
	@echo 'make timing PERIOD=6.666667  : contest 150 MHz'
	@echo 'make sweep   : fixed netlist at 200 / 180 / 160 / 150 MHz'
	@echo 'make waves; make verdi       : generate VCD, then view'
	@echo 'make vectors | package       : verify data / rebuild five verified ZIPs'
	@echo 'make synth; make timing NETLIST=rebuilt : qualify modified RTL'
	@echo 'make timing; make probe      : optional SDF annotation test'
	@echo 'make gate JOBS=4             : optional long 12-layer gate, same PERIOD/NETLIST as timing'
$(TARGETS):
	$(PYTHON) server_eda/daily.py $@ $(ARGS)
sta: timing
check: env run timing report

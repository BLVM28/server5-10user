SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
PERIOD ?= 6.666667
NETLIST ?= fix1
JOBS ?= 4
VEC ?= $(CURDIR)/vec
RUN = $(PYTHON) server_eda/easy.py
ARGS = --period $(PERIOD) --netlist $(NETLIST) --jobs $(JOBS) --vec "$(VEC)"
.PHONY: help env clean compile run regress waves verdi timing sta sweep gate check report synth negative package probe
help:
	@echo 'From this folder: make env; make compile; make run'
	@echo 'make regress      : baseline + all uploaded real-speech RTL vectors'
	@echo 'make negative     : 58 descriptor/address/error/recovery scenarios'
	@echo 'make timing       : final mapped dot/core, SS + FF, 150 MHz'
	@echo 'make synth        : rebuild RTL + original cell repairs; then timing NETLIST=rebuilt'
	@echo 'make sweep        : same mapped netlist at 150 / 140 / 125 MHz'
	@echo 'make gate         : 12 matrices, SS MAX and FF MIN SDF; run timing first'
	@echo 'make package      : refresh separate RTL/TB/Makefile/flow/vector ZIPs'
	@echo 'make probe        : optional short SDF/model compatibility check'
	@echo 'make check        : env + run + timing + report (daily check)'
	@echo 'make waves; make verdi : generate VCD then open wave viewer'
	@echo 'make clean        : archive evidence, remove generated build/manual only'
	@echo 'make timing PERIOD=8.0 / make gate VEC=$$PWD/vec/real_speech/worst'
	@echo 'FAIL gives nonzero exit. CPU/firmware integration remains a separate test.'
env clean compile run regress waves verdi timing sweep gate report synth negative package probe:
	$(RUN) $@ $(ARGS)
sta: timing
check: env run timing report

SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
PERIOD ?= 6.666667
JOBS ?= 2
DAILY := env clean compile run regress waves verdi timing sweep report synth vectors package precision paired
.PHONY: help $(DAILY) sta check acceptance gate_sample power
help:
	@echo 'v4.3: cd /storage2/2026contest/server5/s5_10usr/v4.3'
	@echo 'make compile; make run; make timing; make report'
	@echo 'make waves; make verdi; make regress JOBS=2; make paired'
	@echo 'make gate_sample; make power; make clean (keeps implementation and power)'
	@echo 'PASS/FAIL and NICE cycles/tasks/s are printed; detailed logs stay in build/.'
$(DAILY):
	$(PYTHON) -B server_eda/daily.py $@ --period "$(PERIOD)" --jobs "$(JOBS)"
sta: timing
check: env run timing report
acceptance:
	$(PYTHON) -B server_eda/evidence.py acceptance
gate_sample:
	$(PYTHON) -B server_eda/paired43.py gate --version v43 --corner ss
	$(PYTHON) -B server_eda/paired43.py gate --version v43 --corner ff
power:
	$(PYTHON) -B server_eda/paired43.py power --version v43 --corner ss

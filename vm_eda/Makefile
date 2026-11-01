SHELL := /bin/bash
.ONESHELL:
.PHONY: all v1 v2 functional-v1 functional-v2 check

all: v1 v2

v1 v2:
	set -euo pipefail
	source ./env.sh
	python3 ./run_regression.py $@
	python3 ./run_timing.py $@
	python3 ./close_timing.py $@
	python3 ./audit_sdf.py $@
	python3 ./run_gate.py $@ --eco --corner slow
	python3 ./run_gate.py $@ --eco --corner fast
	python3 ./summarize.py $@

functional-v1 functional-v2:
	set -euo pipefail
	source ./env.sh
	python3 ./run_regression.py $(subst functional-,,$@)

check:
	set -euo pipefail
	source ./env.sh
	python3 ./summarize.py v1
	python3 ./summarize.py v2

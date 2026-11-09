SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
RISCV ?= riscv64-unknown-elf
PAIRED ?= --paired
ABI ?= ../v4.3/integration
RESUME ?=
DC_RESULT ?=
MAPPED_RUN ?=
.PHONY: help firmware compile run primary timing check gate gate-functional
help:
	@echo 'make run                  VCS full regression and P6 paired cycle comparison'
	@echo 'make timing               SMIC40 whole-SoC DC synthesis and 35 PVT/RC checks'
	@echo 'make check                run, timing and worst-setup/worst-hold SDF checks'
	@echo 'make gate-functional MAPPED_RUN=...  mapped VCS functional check without SDF'
	@echo 'make primary              map and diagnose only the primary PVT/RC pair'
	@echo 'make compile              regenerate the shared RTL/synthesis source list'
	@echo 'make firmware RISCV=...  rebuild the RV32 ITCM boot image'
firmware:
	mkdir -p build/fw
	$(RISCV)-gcc -march=rv32imac_zicsr_zifencei -mabi=ilp32 -Os -ffreestanding -fno-builtin -fno-stack-protector -nostdlib -nostartfiles -Wl,--no-relax -T soc/firmware/link.ld -I"$(ABI)" soc/firmware/start.S soc/firmware/main.c -o build/fw/firmware.elf
	$(RISCV)-objcopy -O binary build/fw/firmware.elf build/fw/firmware.bin
	$(PYTHON) -B soc/firmware/bin2hex.py build/fw/firmware.bin soc/firmware/firmware.hex
compile:
	$(PYTHON) -B soc/flow/prepare.py
run:
	$(PYTHON) -B soc/flow/regression.py $(PAIRED)
primary:
	$(PYTHON) -B soc/flow/run_dc.py --primary-only $(if $(RESUME),--resume "$(RESUME)")
timing:
	$(PYTHON) -B soc/flow/run_dc.py $(if $(RESUME),--resume "$(RESUME)")
gate:
	$(PYTHON) -B soc/flow/run_sdf.py $(if $(DC_RESULT),--dc-result "$(DC_RESULT)")
gate-functional:
	@test -n "$(MAPPED_RUN)" || { echo 'Set MAPPED_RUN to the mapped DC run directory'; exit 2; }
	$(PYTHON) -B soc/flow/run_sdf.py --functional "$(MAPPED_RUN)"
check: run timing gate

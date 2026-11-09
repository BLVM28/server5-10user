SHELL := /bin/bash
.DEFAULT_GOAL := help
.NOTPARALLEL:
PYTHON ?= python3
RISCV ?= riscv64-unknown-elf
PAIRED ?= --paired
ABI ?= ../v4.3/integration
RESUME ?=
RETARGET ?=
DC_RESULT ?=
MAPPED_RUN ?=
V44_REFERENCE ?=
WFI_FIRMWARE ?=
PATHS ?= soc/flow/paths.tcl
PERIOD ?= 6.25
.PHONY: help firmware firmware-wfi compile run primary timing period-check period-primary check gate gate-primary gate-functional
help:
	@echo 'make run                  VCS full regression and P6 paired cycle comparison'
	@echo 'make timing               SMIC40 whole-SoC DC synthesis and 35 PVT/RC checks'
	@echo 'make check                run, timing and worst-setup/worst-hold SDF checks'
	@echo 'make gate-functional MAPPED_RUN=...  mapped VCS functional check without SDF'
	@echo 'make gate-primary         diagnostic native SDF at the mapped library pair'
	@echo 'make primary              map and diagnose only the primary PVT/RC pair'
	@echo 'make period-check MAPPED_RUN=... PERIOD=6.666666667  recheck worst corners on the same netlist'
	@echo 'make period-primary MAPPED_RUN=... PERIOD=6.666666667  recheck the primary max/min pair'
	@echo 'PERIOD=6.25               default core clock period in ns (160 MHz)'
	@echo 'make compile              regenerate the shared RTL/synthesis source list'
	@echo 'make firmware RISCV=...  rebuild the RV32 ITCM boot image'
	@echo 'make firmware-wfi RISCV=...  build an isolated timer/WFI self-test image'
firmware:
	mkdir -p build/fw
	$(RISCV)-gcc -march=rv32imac_zicsr_zifencei -mabi=ilp32 -Os -ffreestanding -fno-builtin -fno-stack-protector -nostdlib -nostartfiles -Wl,--no-relax -T soc/firmware/link.ld -I"$(ABI)" soc/firmware/start.S soc/firmware/main.c -o build/fw/firmware.elf
	$(RISCV)-objcopy -O binary build/fw/firmware.elf build/fw/firmware.bin
	$(PYTHON) -B soc/firmware/bin2hex.py build/fw/firmware.bin soc/firmware/firmware.hex
firmware-wfi:
	mkdir -p build/fw
	$(RISCV)-gcc -march=rv32imac_zicsr_zifencei -mabi=ilp32 -Os -ffreestanding -fno-builtin -fno-stack-protector -nostdlib -nostartfiles -Wl,--no-relax -DKWT_TIMER_WFI_SELFTEST -T soc/firmware/link.ld -I"$(ABI)" soc/firmware/start.S soc/firmware/main.c -o build/fw/timer_wfi.elf
	$(RISCV)-objcopy -O binary build/fw/timer_wfi.elf build/fw/timer_wfi.bin
	$(PYTHON) -B soc/firmware/bin2hex.py build/fw/timer_wfi.bin build/fw/timer_wfi.hex
compile:
	$(PYTHON) -B soc/flow/prepare.py
run:
	$(PYTHON) -B soc/flow/regression.py --period "$(PERIOD)" $(PAIRED) $(if $(V44_REFERENCE),--v44-reference "$(V44_REFERENCE)") $(if $(WFI_FIRMWARE),--wfi-firmware "$(WFI_FIRMWARE)")
primary:
	$(PYTHON) -B soc/flow/run_dc.py --paths "$(PATHS)" --period "$(PERIOD)" --primary-only $(if $(RESUME),--resume "$(RESUME)") $(if $(RETARGET),--retarget)
timing:
	$(PYTHON) -B soc/flow/run_dc.py --paths "$(PATHS)" --period "$(PERIOD)" $(if $(RESUME),--resume "$(RESUME)") $(if $(RETARGET),--retarget)
period-check:
	@test -n "$(MAPPED_RUN)" || { echo 'Set MAPPED_RUN to the mapped DC run directory'; exit 2; }
	$(PYTHON) -B soc/flow/run_period_probe.py --paths "$(PATHS)" --mapped "$(MAPPED_RUN)" --period "$(PERIOD)"
period-primary:
	@test -n "$(MAPPED_RUN)" || { echo 'Set MAPPED_RUN to the mapped DC run directory'; exit 2; }
	$(PYTHON) -B soc/flow/run_period_probe.py --paths "$(PATHS)" --mapped "$(MAPPED_RUN)" --period "$(PERIOD)" --primary
gate:
	$(PYTHON) -B soc/flow/run_sdf.py $(if $(DC_RESULT),--dc-result "$(DC_RESULT)")
gate-primary:
	$(PYTHON) -B soc/flow/run_sdf.py --primary-sdf $(if $(DC_RESULT),--dc-result "$(DC_RESULT)")
gate-functional:
	@test -n "$(MAPPED_RUN)" || { echo 'Set MAPPED_RUN to the mapped DC run directory'; exit 2; }
	$(PYTHON) -B soc/flow/run_sdf.py --functional "$(MAPPED_RUN)" --period "$(PERIOD)"
check: run timing gate

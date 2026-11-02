# Forward to the supported version-root Makefile.
.DEFAULT_GOAL := help
.PHONY: all help env clean compile run regress waves verdi synth timing sta sweep gate check report
all: check
help env clean compile run regress waves verdi synth timing sta sweep gate check report:
	$(MAKE) -C .. $@

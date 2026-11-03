.DEFAULT_GOAL := help
TARGETS := help env clean compile run negative regress timing sta sweep report synth waves verdi package vectors precision paired check acceptance gate_sample immediate modes
.PHONY: $(TARGETS)
$(TARGETS):
	$(MAKE) -C .. $@

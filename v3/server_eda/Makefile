.DEFAULT_GOAL := help
TARGETS := help env clean compile run negative regress timing sta sweep report synth waves verdi probe gate package vectors check
.PHONY: $(TARGETS)
$(TARGETS):
	$(MAKE) -C .. $@

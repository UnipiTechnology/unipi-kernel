

PHONY := __all
__all:
	MAKEFLAGS="$(MAKEFLAGS)" $(MAKE) -C linux dtstree=../dts

%:
	MAKEFLAGS="$(MAKEFLAGS)" $(MAKE) -C linux dtstree=../dts $@

# Product -> ordered fragment list mapping lives in configs/products/<product>.mk.
# Each file sets <product>_ARCH and <product>_Fragments.
FRAGDIR  := configs/fragments
PRODUCTS := $(patsubst configs/products/%.mk,%,$(wildcard configs/products/*.mk))
include $(wildcard configs/products/*.mk)
# Target stem, with the "unipi-" prefix stripped for product targets.
PROD = $(patsubst unipi-%,%,$*)

# Build a product's .config by merging its fragments (no committed defconfig).
%_defconfig:
	@python3 configs/configtool.py gen \
		--arch $($(PROD)_ARCH) \
		$(addprefix $(FRAGDIR)/,$($(PROD)_Fragments))

# Compare the current linux/.config against the fragments (read-only).
report-%:
	@python3 configs/configtool.py report --config linux/.config \
		$(addprefix $(FRAGDIR)/,$($(PROD)_Fragments))

# Validate a product's fragments.
check-%:
	@python3 configs/configtool.py check $(addprefix $(FRAGDIR)/,$($(PROD)_Fragments))

check-fragments: $(addprefix check-,$(PRODUCTS))
	@echo "all fragment checks passed"

clean:
	@find dts -name .\* -exec rm \{\} \;
	@find dts -name \*.dtb -exec rm \{\} \;
	MAKEFLAGS="$(MAKEFLAGS)" $(MAKE) -C linux $@

mrproper:
	@find dts -name .\* -exec rm \{\} \;
	@find dts -name \*.dtb -exec rm \{\} \;
	MAKEFLAGS="$(MAKEFLAGS)" $(MAKE) -C linux $@

scmversion:
	@ # create empty .scmversion to remove + sign from kernelrelease
	@ :> linux/.scmversion

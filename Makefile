

PHONY := __all
__all:
	MAKEFLAGS="$(MAKEFLAGS)" $(MAKE) -C linux dtstree=../dts

%:
	MAKEFLAGS="$(MAKEFLAGS)" $(MAKE) -C linux dtstree=../dts $@

%_defconfig:
	MAKEFLAGS="$(MAKEFLAGS)" $(MAKE) -C linux KBUILD_DEFCONFIG=../../../../configs/$@ defconfig

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

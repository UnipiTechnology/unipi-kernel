# Unipi Zulu (NXP i.MX8M Mini) — ordered kernel config fragments.
# Consumed by the root Makefile's %_defconfig / report-% / check-% rules.
zulu_ARCH      := arm64
zulu_Fragments := \
	00-arm64.config \
	05-core.config \
	10-storage.config \
	15-net.config \
	30-usb.config \
	35-peripherals.config \
	50-soc-imx8mm.config

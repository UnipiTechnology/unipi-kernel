# Unipi G1 (Rockchip RK3328) — ordered kernel config fragments.
# Consumed by the root Makefile's %_defconfig / report-% / check-% rules.
g1_ARCH      := arm64
g1_Fragments := \
	00-arm64.config \
	05-core.config \
	10-storage.config \
	15-net.config \
	16-net-bonding.config \
	30-usb.config \
	35-peripherals.config \
	50-soc-rockchip.config

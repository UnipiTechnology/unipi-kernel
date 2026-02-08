# Linux kernel for Unipi PLCs

This repo contains recipes and patches to build Linux kernel
for Unipi PLCs and SBC
 
 - Unipi Zulu - mini SBC with NXP i.MX8M Mini
 - Unipi Patron - PLC with Unipi Zulu
 - Unipi G1 - PLC with Rockchip RK3328 (Not finished yet!)
 - Unipi Edge - PLC with Raspberry Pi CM40 (Not finished yet!)

Build is based on [Linux v6.12.66-cip16](https://git.kernel.org/pub/scm/linux/kernel/git/cip/linux-cip.git)

## How to cross-build kernel on Linux host

Required packages - package names are valid for Debian 13
 - build-essential
 - git
 - bison
 - flex
 - crossbuild-essential-arm64
 - libssl-dev
 - libncurses-dev
 - bc
 - wget

### Prepare building environment

Load source repo on unipi-kernel and download all required sources
```
git clone https://github.com/UnipiTechnology/unipi-kernel.git
cd unipi-kernel/
./prepare.sh build
```

### Compile binaries

Use prepared configuration file for Unipi Zulu.
```
  CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 make unipi-zulu_defconfig
```

To modifying U-boot building options use menuconfig.
```
CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 make menuconfig
```
Build kernel, modules and devicetree binaries
```
CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 make -j <num_of_proc>
```

### Installation

Create some directory on filesystem for example /i and copy build artifacts there
```
mkdir /i
CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 make install INSTALL_PATH=/i
CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 make dtbs_install INSTALL_DTBS_PATH=/i
CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 make modules_install INSTALL_MOD_PATH=/i
```

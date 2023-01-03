#!/bin/bash
set -xe

SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`
CONFIG_FILE=${SCRIPT_DIR}/config.env

# Load config.env file
if [ -f ${CONFIG_FILE} ] ; then
    source ${CONFIG_FILE}
fi

# Check variables
if [ -z "$KERNEL_VERSION" ] ; then
    KERNEL_VERSION="5.15.28"
fi

WORKING_DIR=${SCRIPT_DIR}/work
LINUX_DIR=${WORKING_DIR}/linux-${KERNEL_VERSION}
OVERLAY_KERNEL=${SCRIPT_DIR}/overlay-kernel
MAKE_OPTIONS="-j$(nproc) ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -C ${LINUX_DIR}"
KERNEL=kernel8

# Get and extract sources
wget https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-${KERNEL_VERSION}.tar.xz -O ${WORKING_DIR}/linux-${KERNEL_VERSION}.tar.xz
tar xf ${WORKING_DIR}/linux-${KERNEL_VERSION}.tar.xz -C ${WORKING_DIR}

# Use COGIP config
cp defconfig ${LINUX_DIR}/arch/arm64/configs/cogip_defconfig

# Configure and build
make ${MAKE_OPTIONS} cogip_defconfig
make ${MAKE_OPTIONS} Image modules dtbs

rm -rf ${OVERLAY_KERNEL}
mkdir -p ${OVERLAY_KERNEL}/boot/overlays

# Get latest GPU firmware
wget https://github.com/raspberrypi/firmware/raw/master/boot/start4.dat -O ${OVERLAY_KERNEL}/boot/start4.elf
wget https://github.com/raspberrypi/firmware/raw/master/boot/fixup4.dat -O ${OVERLAY_KERNEL}/boot/fixup4.dat

# Install kernel, modules and dts
make ${MAKE_OPTIONS} INSTALL_MOD_PATH=${OVERLAY_KERNEL} modules_install
cp ${WORKING_DIR}/linux-${KERNEL_VERSION}/arch/arm64/boot/Image ${OVERLAY_KERNEL}/boot/$KERNEL.img
cp ${WORKING_DIR}/linux-${KERNEL_VERSION}/arch/arm64/boot/dts/broadcom/*.dtb ${OVERLAY_KERNEL}/boot/
cp -f ${WORKING_DIR}/linux-${KERNEL_VERSION}/arch/arm64/boot/dts/overlays/*.dtb* ${OVERLAY_KERNEL}/boot/overlays/ || true
cp -f ${WORKING_DIR}/linux-${KERNEL_VERSION}/arch/arm64/boot/dts/overlays/README ${OVERLAY_KERNEL}/boot/overlays/ || true

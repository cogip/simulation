#!/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`
source ${SCRIPT_DIR}/common.sh

WORKING_DIR=${SCRIPT_DIR}/work
MOUNT_DIR=${WORKING_DIR}/mnt
ROOTFS=${WORKING_DIR}/rootfs.tar
RASPIOS_ZIP=$(basename -- ${RASPIOS_URL})
RASPIOS_EXTENSION="${RASPIOS_ZIP##*.}"
RASPIOS_LITE_IMG=${WORKING_DIR}/$(echo ${RASPIOS_ZIP} | cut -d . -f 1).img

mkdir -p ${WORKING_DIR}
mkdir -p ${MOUNT_DIR}
rm -rf ${RASPIOS_LITE_IMG} ${ROOTFS}

# Get Raspberry Pi OS image
wget -c ${RASPIOS_URL} -O ${WORKING_DIR}/${RASPIOS_ZIP}

if [ "$RASPIOS_EXTENSION" = "zip" ]; then
    unzip ${WORKING_DIR}/${RASPIOS_ZIP} -d ${WORKING_DIR}
else
    unxz -k ${WORKING_DIR}/${RASPIOS_ZIP}
fi

# Mount image on loopback device
losetup -a | grep "${RASPIOS_LITE_IMG}" | awk -F: '{ print $1 }' | xargs -r sudo losetup -d
loop_dev=$(sudo losetup -fP --show ${RASPIOS_LITE_IMG})

# Extract rootfs and boot
sudo mount ${loop_dev}p2 ${MOUNT_DIR}
sudo rm -rf "${MOUNT_DIR}/boot/firmware/"
sudo mkdir -p "${MOUNT_DIR}/boot/firmware"
sudo mount ${loop_dev}p1 ${MOUNT_DIR}/boot/firmware
sudo tar cf ${ROOTFS} -C ${MOUNT_DIR} --numeric-owner .
sudo umount ${MOUNT_DIR}/boot/firmware
sudo umount ${MOUNT_DIR}
sudo chown $(whoami) ${ROOTFS}

# Unmount loop device
sudo losetup -d ${loop_dev}

# Create a Docker image from scratch using extracted rootfs
DOCKER_BUILDKIT=1 docker build --progress plain . -f Dockerfile.base -t cogip/raspios:base

rm -rf ${ROOTFS}

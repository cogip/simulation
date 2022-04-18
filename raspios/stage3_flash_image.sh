#!/bin/bash
set -xe

sudo -v

SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`
ENV_FILE=${SCRIPT_DIR}/.env

# Load .env file
if [ -f ${ENV_FILE} ] ; then
    source ${ENV_FILE}
fi

# Check variables
if [ -z "${SDCARD_DEV}" ] ; then
    echo "Error: Variable SDCARD_DEV not defined (in .env file)"
    exit 1
fi
if [ ! -b "${SDCARD_DEV_BOOT}" ] ; then
    echo "Error: ${SDCARD_DEV_BOOT} not found"
    exit 1
fi
if [ -z "${SDCARD_DEV_ROOTFS}" ] ; then
    echo "Error: Variable SDCARD_DEV_ROOTFS not defined (in .env file)"
    exit 1
fi
if [ ! -b "${SDCARD_DEV_BOOT}" ] ; then
    echo "Error: ${SDCARD_DEV_BOOT} not found"
    exit 1
fi
if [ ! -b "${SDCARD_DEV_ROOTFS}" ] ; then
    echo "Error: ${SDCARD_DEV_ROOTFS} not found"
    exit 1
fi

WORKING_DIR=${SCRIPT_DIR}/work
RASPIOS_COGIP_IMG="${WORKING_DIR}/raspios-bullseye-arm64-cogip.img"
if [ ! -d "${WORKING_DIR}" ] ; then
    echo "Error: ${WORKING_DIR} not found"
    exit 1
fi
if [ ! -f "${RASPIOS_COGIP_IMG}" ] ; then
    echo "Error: ${RASPIOS_COGIP_IMG} not found"
    exit 1
fi

sudo umount ${SDCARD_DEV_BOOT} || true
sudo umount ${SDCARD_DEV_ROOTFS} || true
sudo dd if=${RASPIOS_COGIP_IMG} of=${SDCARD_DEV} bs=4M status=progress
sync
sudo umount ${SDCARD_DEV_BOOT} || true
sudo umount ${SDCARD_DEV_ROOTFS} || true
sudo parted ${SDCARD_DEV} --script "resizepart 2 -1"
sudo e2fsck -f ${SDCARD_DEV_ROOTFS}
sudo resize2fs ${SDCARD_DEV_ROOTFS}

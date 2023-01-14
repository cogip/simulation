#!/bin/bash
set -xe

sudo -v

SCRIPT=$(readlink -f $0)
SCRIPT_DIR=`dirname $SCRIPT`
CONFIG_FILE=${SCRIPT_DIR}/config.env

# Load config.env file
if [ -f ${CONFIG_FILE} ] ; then
    source ${CONFIG_FILE}
fi

source ${SCRIPT_DIR}/utils.sh

ROBOT_ID=$(get_robot_id $@)

# Check variables
check_vars SDCARD_DEV SDCARD_DEV_BOOT SDCARD_DEV_ROOTFS SDCARD_DEV_BOOT SDCARD_DEV_ROOTFS

# Variables depending on robot id
if ((${ROBOT_ID} == 0))
then
    DOCKER_TAG=beacon
    HOSTNAME=beacon
else
    DOCKER_TAG=robot
    HOSTNAME=robot${ROBOT_ID}
fi

WORKING_DIR=${SCRIPT_DIR}/work
RASPIOS_COGIP_IMG="${WORKING_DIR}/raspios-bullseye-arm64-${HOSTNAME}.img"
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

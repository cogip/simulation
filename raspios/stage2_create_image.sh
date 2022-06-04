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
if [ -z "${IP_ADDRESS}" ] ; then
    echo "Error: Variable IP_ADDRESS not defined (in .env file)"
    exit 1
fi
if [ -z "${GATEWAY}" ] ; then
    echo "Error: Variable GATEWAY not defined (in .env file)"
    exit 1
fi
if [ -z "${WLAN_SSID}" ] ; then
    echo "Error: Variable WLAN_SSID not defined (in .env file)"
    exit 1
fi
if [ -z "${WLAN_PSK}" ] ; then
    echo "Error: Variable WLAN_PSK not defined (in .env file)"
    exit 1
fi

WORKING_DIR=${SCRIPT_DIR}/work
OVERLAY_ROOTFS=${SCRIPT_DIR}/overlay-rootfs
OVERLAY_KERNEL=${SCRIPT_DIR}/overlay-kernel
MOUNT_DIR=${WORKING_DIR}/mnt
RASPIOS_COGIP_IMG="${WORKING_DIR}/raspios-bullseye-arm64-cogip.img"
ROOTFS=${WORKING_DIR}/rootfs-custom.tar
RSYNC_FLAGS="-vh --progress --modify-window=1 --recursive --ignore-errors"

rm -rf ${RASPIOS_COGIP_IMG} ${ROOTFS}

# Extract rootfs
container=$(docker run -d cogip/raspios:custom sleep infinity)
docker export -o ${ROOTFS} ${container}
docker rm -f ${container}

# Build custom image
ALIGN="$((4 * 1024 * 1024))"

BOOT_SIZE="$((256 * 1024 * 1024))"
ROOTFS_SIZE=$(du --apparent-size -s --block-size=1 ${ROOTFS} | cut -f 1)
ROOT_MARGIN="$(echo "($ROOTFS_SIZE * 0.2 + 200 * 1024 * 1024) / 1" | bc)"
BOOT_PART_START=$((ALIGN))
BOOT_PART_SIZE=$(((BOOT_SIZE + ALIGN - 1) / ALIGN * ALIGN))
ROOT_PART_START=$((BOOT_PART_START + BOOT_PART_SIZE))
ROOT_PART_SIZE=$(((ROOTFS_SIZE + ROOT_MARGIN + ALIGN  - 1) / ALIGN * ALIGN))
IMG_SIZE=$((BOOT_PART_START + BOOT_PART_SIZE + ROOT_PART_SIZE))

rm -rf ${RASPIOS_COGIP_IMG}
truncate -s ${IMG_SIZE} ${RASPIOS_COGIP_IMG}

parted --script "${RASPIOS_COGIP_IMG}" mklabel msdos
parted --script "${RASPIOS_COGIP_IMG}" unit B mkpart primary fat32 "${BOOT_PART_START}" "$((BOOT_PART_START + BOOT_PART_SIZE - 1))"
parted --script "${RASPIOS_COGIP_IMG}" unit B mkpart primary ext4 "${ROOT_PART_START}" "$((ROOT_PART_START + ROOT_PART_SIZE - 1))"

PARTED_OUT=$(parted -sm "${RASPIOS_COGIP_IMG}" unit b print)
BOOT_OFFSET=$(echo "$PARTED_OUT" | grep -e '^1:' | cut -d':' -f 2 | tr -d B)
BOOT_LENGTH=$(echo "$PARTED_OUT" | grep -e '^1:' | cut -d':' -f 4 | tr -d B)

ROOT_OFFSET=$(echo "$PARTED_OUT" | grep -e '^2:' | cut -d':' -f 2 | tr -d B)
ROOT_LENGTH=$(echo "$PARTED_OUT" | grep -e '^2:' | cut -d':' -f 4 | tr -d B)

BOOT_DEV=$(sudo losetup --show -f -o "${BOOT_OFFSET}" --sizelimit "${BOOT_LENGTH}" "${RASPIOS_COGIP_IMG}")
ROOT_DEV=$(sudo losetup --show -f -o "${ROOT_OFFSET}" --sizelimit "${ROOT_LENGTH}" "${RASPIOS_COGIP_IMG}")

ROOT_FEATURES="^huge_file"
for FEATURE in metadata_csum 64bit; do
    if grep -q "$FEATURE" /etc/mke2fs.conf; then
        ROOT_FEATURES="^$FEATURE,$ROOT_FEATURES"
    fi
done

sudo mkdosfs -n boot -F 32 -v "$BOOT_DEV"
sudo mkfs.ext4 -L rootfs -O "$ROOT_FEATURES" "$ROOT_DEV"

sudo mount -v "$ROOT_DEV" "${MOUNT_DIR}" -t ext4
sudo mkdir -p "${MOUNT_DIR}/boot"
sudo mount -v "$BOOT_DEV" "${MOUNT_DIR}/boot" -t vfat

sudo tar xf ${ROOTFS} -C ${MOUNT_DIR} --numeric-owner
if [ -d "${OVERLAY_KERNEL}" ] ; then
    sudo rsync ${RSYNC_FLAGS} ${OVERLAY_KERNEL}/ ${MOUNT_DIR}/
fi
sudo cp ${OVERLAY_ROOTFS}/etc/hostname ${MOUNT_DIR}/etc/hostname
sudo cp ${OVERLAY_ROOTFS}/etc/hosts ${MOUNT_DIR}/etc/hosts

# Fix boot and root devices
IMGID="$(dd if="${RASPIOS_COGIP_IMG}" skip=440 bs=1 count=4 2>/dev/null | xxd -e | cut -f 2 -d' ')"
sudo sed -i "s/ROOTDEV/PARTUUID=${IMGID}/" ${MOUNT_DIR}/etc/fstab
sudo sed -i "s/ROOTDEV/PARTUUID=${IMGID}/" ${MOUNT_DIR}/boot/cmdline.txt

# Apply custom parameters
sudo sed -i "s/IP_ADDRESS/${IP_ADDRESS}/" ${MOUNT_DIR}/etc/network/interfaces.d/wlan0
sudo sed -i "s/GATEWAY/${GATEWAY}/" ${MOUNT_DIR}/etc/network/interfaces.d/wlan0
sudo sed -i "s/WLAN_SSID/${WLAN_SSID}/" ${MOUNT_DIR}/etc/wpa_supplicant/wpa_supplicant.conf
sudo sed -i "s/WLAN_PSK/${WLAN_PSK}/" ${MOUNT_DIR}/etc/wpa_supplicant/wpa_supplicant.conf

sudo umount ${MOUNT_DIR}/boot
sudo umount ${MOUNT_DIR}
sudo zerofree "${ROOT_DEV}"
sync
sudo losetup -d ${BOOT_DEV}
sudo losetup -d ${ROOT_DEV}

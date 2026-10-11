#!/bin/bash
# Pin the Raspberry Pi bootloader EEPROM firmware into the image so the chosen
# version is flashed ONCE at first boot. The bootROM, at boot, runs recovery.bin
# from the boot partition: it verifies pieeprom.sig, flashes pieeprom.upd, then
# renames recovery.bin -> recovery.000 and resets (pre-OS, no systemd, one-shot).
# rpi-eeprom stays purged (no apt self-update, no silent downgrade); this is the
# deliberate frozen counterpart. RPi only (Pi4 = bcm2711, Pi5 = bcm2712).
#
# Blobs come from raspberrypi/rpi-eeprom at a pinned release tag, cached under
# ${EEPROM_CACHE} (a present file is not re-downloaded). Sourced by build.sh;
# uses BOARD/TARGET/SCRIPT_DIR/UP. Staged into the base overlay (per TARGET soc).

# --- pinned release (latest of each SoC as of 2026-10-11; bump tag + date together) ---
EEPROM_2712_TAG="v2026.09.25-2712"                               # Pi5
EEPROM_2712_PIEEPROM="firmware-2712/default/pieeprom-2026-09-25.bin"
EEPROM_2711_TAG="v2026.09.23-2711-0138c0"                        # Pi4
EEPROM_2711_PIEEPROM="firmware-2711/default/pieeprom-2026-09-23.bin"

EEPROM_CACHE="${EEPROM_CACHE:-${SCRIPT_DIR}/.cache/eeprom}"
EEPROM_RAW="https://raw.githubusercontent.com/raspberrypi/rpi-eeprom"

# Echo "<soc> <tag> <pieeprom-path>" for this TARGET, nothing on a non-RPi board.
# beacon = Pi5 (2712), every other RPi target (robot/pami) = Pi4 (2711).
_cogip_eeprom_pin() {
    [ "${BOARD}" = "rpi4b" ] || return 0
    if [ "${TARGET}" = "beacon" ]; then
        printf '2712 %s %s\n' "${EEPROM_2712_TAG}" "${EEPROM_2712_PIEEPROM}"
    else
        printf '2711 %s %s\n' "${EEPROM_2711_TAG}" "${EEPROM_2711_PIEEPROM}"
    fi
}

# Base-hash contribution: the pin line only, so bumping the version busts the base.
cogip_eeprom_hash() { _cogip_eeprom_pin; }

# Download URL part -> file, skipping a non-empty cached file.
_cogip_eeprom_get() {
    local out="$2"
    [ -s "${out}" ] && return 0
    echo "Fetching EEPROM blob: $1"
    curl -fsSL -o "${out}.tmp" "${EEPROM_RAW}/$1" && mv "${out}.tmp" "${out}" \
        || { rm -f "${out}.tmp"; echo "EEPROM fetch failed: ${EEPROM_RAW}/$1" >&2; return 1; }
}

# Fetch (cached) recovery.bin + pieeprom, generate pieeprom.sig, stage the trio
# into the base overlay at usr/local/lib/cogip-eeprom/. No-op off rpi4b.
cogip_stage_eeprom() {
    local pin; pin=$(_cogip_eeprom_pin) || return 0
    [ -n "${pin}" ] || return 0
    local soc tag pie; read -r soc tag pie <<<"${pin}"
    local cdir="${EEPROM_CACHE}/${tag}"
    mkdir -p "${cdir}"
    local pie_bin="${cdir}/$(basename "${pie}")" recov_bin="${cdir}/recovery-${soc}.bin"
    _cogip_eeprom_get "${tag}/${pie}" "${pie_bin}"
    _cogip_eeprom_get "${tag}/firmware-${soc}/default/recovery.bin" "${recov_bin}"

    local dst="${UP}/overlay/usr/local/lib/cogip-eeprom"
    rm -rf "${dst}"; mkdir -p "${dst}"
    cp "${recov_bin}" "${dst}/recovery.bin"
    cp "${pie_bin}"   "${dst}/pieeprom.upd"
    # Unsigned 3-line .sig, same format rpi-eeprom-digest writes: sha256 digest +
    # update-timestamp + target-soc. recovery.bin checks it before flashing (a
    # corruption guard, not security). ts fixed to the image date = reproducible.
    {
        sha256sum "${dst}/pieeprom.upd" | awk '{print $1}'
        local d; d=$(basename "${pie}" .bin); d=${d#pieeprom-}
        printf 'ts: %s\n' "$(date -u -d "${d}" +%s 2>/dev/null || echo 0)"
        printf 'target-soc: %s\n' "${soc}"
    } > "${dst}/pieeprom.sig"
    echo "EEPROM pinned: ${tag} $(basename "${pie}") (bcm${soc})."
}

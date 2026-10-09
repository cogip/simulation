#!/bin/bash
# Target: beacon (ROBOT_ID=0) - server-beacon + dashboard + kiosk + AP (dnsmasq).
# Runs its own server, not the robot core. Sourced by customize-image.sh (chroot).
TARGET_PACKAGES="${KIOSK_PACKAGES} ntpsec dnsmasq iptables ifmetric"
# libcamera CLI (`cam`) to test the Pi5 imx708 (RP1 CFE + PiSP). The coherent
# libcamera is 0.7.1 from trixie-backports (the rpt 0.7.2 is uninstallable).
# beaconcam itself grabs frames via V4L2, so no python3-libcamera here.
TARGET_BACKPORTS_PACKAGES="libcamera0.7 libcamera-ipa libcamera-tools"

enable_services() {
    systemctl enable ntpsec
    systemctl disable systemd-resolved 2>/dev/null || true
    systemctl enable dnsmasq
    systemctl enable cogip-server-beacon cogip-dashboard weston.service
    systemctl set-default graphical.target
    # IP forwarding + NAT (iptables restored by rc.local at boot); the eth0 /
    # dnsmasq IP_ADDRESS placeholder is filled by the provision step.
    chmod +x /etc/rc.local 2>/dev/null || true
    systemctl enable rc-local.service 2>/dev/null || true
}

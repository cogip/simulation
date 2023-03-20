#!/bin/bash

#sudo ip route add 192.168.2.0/24 via 192.168.1.199

function trap_ctrlc ()
{
    killall -TERM cogip-monitor
    killall -TERM cogip-copilot
    killall -TERM cogip-server
    killall -TERM cogip-planner
    killall -TERM cogip-detector
    #killall -TERM make

    exit 0
}

trap "trap_ctrlc" 2

mkdir -p /tmp/socat
socat pty,raw,echo=0,link=/tmp/socat/ttySTM32 pty,raw,echo=0,link=/tmp/socat/ttyRPI &

#make -C ../mcu-firmware/applications/app_test BOARD=cogip-native all -j
#mate-terminal --command="make -C ../mcu-firmware/applications/app_test BOARD=cogip-native PORT=\"-c /dev/null -c /tmp/ttySTM32\" term" &

cogip-server &
cogip-planner &
cogip-copilot -p /tmp/socat/ttyRPI &
cogip-detector &
cogip-monitor http://localhost:8080 &

#cogip-monitor http://192.168.1.199:8080 &

sleep infinity


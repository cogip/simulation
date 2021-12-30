# Copilot

The Copilot tools is running on a Raspberry Pi embedded in the robot.
It communicates with the robot's STM32 over a serial port.
It is connected to the network over Wifi.
It provides a Socket.IO server to send shell menus and robot states to monitors connected
to this server and receive commands from monitors.
It provides a web server to provide monitoring on any devices (PC, smartphones)
connected to the same network.

## Command line options

```bash
$ cogip-copilot --help
Usage: cogip-copilot [OPTIONS]

Launch COGIP Copilot.

Options:
  -s, --serial PATH               Serial port connected to STM32 device  [default: /dev/ttyUSB0]
  -b, --baud INTEGER              Baud rate  [default: 230400]
  -p, --port INTEGER              Socket.IO/Web server port  [default: 80]
```

# Copilot

The Copilot tools is running on a Raspberry Pi embedded in the robot.
It communicates with the robot's STM32 over a serial port.
It is connected to the network over Wifi.
It provides a Socket.IO server to send shell menus and robot states to monitors connected
to this server and receive commands from monitors.
It provides a web server to provide monitoring on any devices (PC, smartphones)
connected to the same network.

## Run Copilot

```bash
$ cogip-copilot
```

## Parameters

Copilot default parameters can be modified using environment variables.
All variables can be defined in the `.env` file.

Example of `.env` file with all default values:

```bash
# Socket.IO/Web server port
COPILOT_SERVER_PORT=8080

# Serial port connected to STM32 device
COPILOT_SERIAL_PORT="/dev/ttyUSB0"

# Baud rate
COPILOT_SERIAL_BAUD=230400
```

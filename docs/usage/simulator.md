# Simulator

After installation and firmware compilation (see [Install](../install.md)), the simulator
is launched with:
```bash
$ simulator
```

The simulator can be used with the native firmware or connected via serial port to the robot (locally or on a remote device).

By default, the serial ports are scanned, and if found, the first port will be used to try to connect to the robot (see [Monitoring Mode](#monitor-mode)).

If no serial port is found, it will launch the default native firmware (see [Simulation Mode](#simulation-mode)).


## Command line options

```bash
$ simulator --help
usage: simulator [-h] [-D UART_DEVICE | -B NATIVE_BINARY | -r REMOTE]

Launch COGIP Simulator.

optional arguments:
  -h, --help            show this help message and exit
  -D UART_DEVICE, --device UART_DEVICE
                        Specify UART device
  -B NATIVE_BINARY, --binary NATIVE_BINARY
                        Specify native binary compiled with shell menus enabled
  -r REMOTE, --remote REMOTE
                        Remote device providing the serial port connected to the robot
```

## Simulation Mode

The default native firmware is:
`submodules/mcu-firmware/applications/cup2019/bin/cogip-native/cortex.elf`

It can be changed using:

  * the CLI option: `-B/--binary <NATIVE_BINARY>`

  * the environment variable: `NATIVE_BINARY`

Using these options will disable serial port scan.

## Monitoring Mode

If a robot is connected to a serial port, the first port will be used by default.

The default serial port can be modified using the environment variable `DEFAULT_UART`.

To specify an other serial port, use the `-D/--device <UART_DEVICE>` CLI option.

## Remote Mode

If a robot is connected to a serial port on a remote device, use `-r/--remote <REMOTE>`
to specify this device.

The argument must identify a device that can be connected using `ssh` without password.

`picocom` must be installed on the remote device. Serial port must be `/dev/ttyACM0`.

## Environment Variables

!!! note "Environnement variables are case-insentive."

!!! note "Environnement variables can be set in the `.env` file."

Environment variables are defined in the [`Settings`][cogip.config.Settings] class.

# Usage

After installation and firmware compilation (see [Install](install.md)), the simulator
is launched with:
```bash
$ simulator
```

The simulator can be used with the native firmware or connected via serial port to the robot.

By default, the serial ports are scanned, and if found, the first port will be used to try to connect to the robot (see [Robot Mode](#robot-mode)).

If no serial port is found, it will launch the default native firmware (see [Native Mode](#native-mode)).


## Command line options

```bash
$ simulator --help
usage: simulator [-h] [-D UART_DEVICE | -B NATIVE_BINARY]

Launch COGIP Simulator.

optional arguments:
  -h, --help            show this help message and exit
  -D UART_DEVICE, --device UART_DEVICE
                        Specify UART device
  -B NATIVE_BINARY, --binary NATIVE_BINARY
                        Specify native board binary compiled in calibration mode
```

## Native Mode

The default native firmware is:
`submodules/mcu-firmware/applications/cogip2019-cortex/bin/cogip2019-cortex-native/cortex.elf`

It can be changed using:

  * the CLI option: `-B/--binary <NATIVE_BINARY>`

  * the environment variable: `NATIVE_BINARY`

Using these options will disable serial port scan.

## Robot Mode

If a robot is connected to a serial port, the first port will be used by default.

The default serial port can be modified using the environment variable `DEFAULT_UART`.

To specify an other serial port, use the `-D/--device <UART_DEVICE>` CLI option.

## Environment Variables

!!! note "Environnement variables are case-insentive."

!!! note "Environnement variables can be set in the `.env` file."

Environment variables are defined in the [`Settings`][cogip.config.Settings] class.

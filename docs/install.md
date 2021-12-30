# Installation

## OS

Linux only.

Tested on Ubuntu 20.04.
The firmware compiled in native mode is not compatible with Ubuntu 20.10+.

Any Linux distribution with Python 3.8+ properly installed should be compatible.

## Git LFS

This repository uses Git LFS to store asset files for the robot and table.
You should first install and initialize git-lfs:

```bash
sudo apt install git-lfs
git lfs install
git lfs pull
```

## Git Submodules

The simulation tools depend on the compatible version of [cogip/mcu-firmware](https://github.com/cogip/mcu-firmware) which also depends on a specific version of [RIOT-OS/RIOT](https://github.com/RIOT-OS/RIOT). So to avoid struggle in finding the correct versions of the dependencies, we use git submodules to fix the versions of `mcu-firmware` and `RIOT`.
Do not forget to fetch the submodules after `git clone`:

```bash
git submodule update --init
```

## Debian packages

```bash
sudo apt install python3.8 python3.8-dev python3-venv libxcb-xinerama0 socat protobuf-compiler
```

## Build mcu-firmware

See the `Requirements` section of `submodules/mcu-firmware/README.md` to setup the build environment.

Use the following command to build the native version of the firmware:

### Native build

```bash
# For the robot firmware
make -C submodules/mcu-firmware/applications/cup2021 BOARD=cogip-native

# For the test platform
make -C submodules/mcu-firmware/applications/app_test BOARD=cogip-native
```

### ARM build

Use the following command to build the ARM version of the firmware:

```bash
# For the robot firmware
make -C submodules/mcu-firmware/applications/cup2021 BOARD=cogip-cortex

# For the test platform
make -C submodules/mcu-firmware/applications/app_test BOARD=cogip-nucleo-f446re
```

## Installation

All tools can be install on the development PC.

!!! note "Python 3.8 or more is required."

To setup a new environment, create a virtual env and install the package in dev mode:
```bash
python3.8 -m venv venv
source venv/bin/activate
pip install -U pip
pip install wheel
pip install -e .
```

`mcu-firmware` and `Copilot`  can be run on the development PC.
In this case, we have to create virtual serial ports to simulation the serial link between STM32 and Raspberry Pi:

```bash
socat pty,raw,echo=0,link=/tmp/ttySTM32 pty,raw,echo=0,link=/tmp/ttyRPI
```

Native firmware is then run using:

```bash
make -C submodules/mcu-firmware/applications/app_test BOARD=cogip-native PORT="-c /dev/null -c /tmp/ttySTM32" term
```

!!! note "In RIOT, `-c` option specifies serial ports to use. First port being used for the shell, it is not configurable, so we just pass `/dev/null`."

`Copilot` is run using:

```bash
cogip-copilot -s /tmp/ttyRPI -p 8080
```

And finally `Monitor`is launched using:

```bash
cogip-monitor http://localhost:8080
```

## Packaging

To build a source distribution package, use:

```bash
python setup.py sdist
```

This will produce `dist/cogip-tools-1.0.0.tar.gz`.
This package can be copied to the Raspberry Pi and installed to deploy the `Copilot`.

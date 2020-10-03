# Installation

## OS

Linux only.

Tested on Ubuntu 20.04.

Any Linux distribution with Python 3.8 properly installed should be compatible.

## Git LFS

This repository uses Git LFS to store asset files for the robot and table.
You should first install and initialize git-lfs:
```bash
sudo apt install git-lfs
git lfs install
git lfs pull
```

## Git Submodules

The simulation depends on the compatible version of [cogip/mcu-firmware](https://github.com/cogip/mcu-firmware) which also depends on a specific version of [RIOT-OS/RIOT](https://github.com/RIOT-OS/RIOT). So to avoid struggle in finding the correct versions of the dependencies, we use git submodules to fix the versions of `mcu-firmware` and `RIOT`. 
Do not forget to fetch the submodules after `git clone`:
```bash
git submodule update --init
```

## Build mcu-firmware

See the `Requirements` section of `submodules/mcu-firmware/README.md` to setup the build environment.

Use the following command to build the native version of the firmware:

```bash
make -C submodules/mcu-firmware/applications/cogip2019-cortex BOARD=cogip2019-cortex-native MCUFIRMWARE_OPTIONS=calibration
```

The variable `QUIET=0` can be added to display compilation commands.

## Debian packages

```bash
sudo apt install python3.8 python3.8-dev python3-venv libxcb-xinerama0 socat
```

## Installation

!!! note "Python 3.8 or more is required."

To setup a new environment, create a virtual env and install the package in dev mode:
```bash
python3.8 -m venv venv
source venv/bin/activate
pip install wheel
pip install -e .
```

This will install the simulator in developer mode and all its dependencies.

## Assets

The asset files for table and robot are loaded by default in `assets`.
It can be adjusted using command line options (`bin/simulator.py --help` for more information).
The asset format currently supported is Collada (`.dae`).

## Launch

Run `simulator` to launch the simulator.

# Setup

There are two ways to setup the environment to develop and run the tools.

- The [Manual method](#manual-method) requires to configure the environment on the development computer and to run tools one by one.
This method also briefly explains how to build the firmware for the real MCU.

- The [Docker method](#docker-method) provides a complete Docker Compose stack that configure, compile and run each tool using only one command.

To prepare SDCards for Raspberry Pi SDCards for robots and beacon, refer to the [Raspberry Pi OS section](raspios.md).

## Common Setup

### OS

Linux only.

Tested on Ubuntu 23.04 (with Xorg instead of Wayland for proper display of the Monitor).

### Debian packages

```bash
sudo apt install python3 git build-essential
```

### Git Submodules

The simulation tools depend on the compatible version of [cogip/mcu-firmware](https://github.com/cogip/mcu-firmware) which also depends on a specific version of [RIOT-OS/RIOT](https://github.com/RIOT-OS/RIOT). So to avoid struggle in finding the correct versions of the dependencies, we use git submodules to fix the versions of `mcu-firmware` and `RIOT`.
Do not forget to fetch the submodules after `git clone`:

```bash
git submodule update --init
```

## Manual Method

### Python

Python 3.11+ is required.

### Debian packages

```bash
sudo apt install python3-dev python3-venv libxcb-xinerama0 socat protobuf-compiler build-essential swig cmake pkg-config
```

### Build mcu-firmware

See the `Requirements` section of `submodules/mcu-firmware/README.md` to setup the build environment.

Use the following command to build the native version of the firmware:

#### Native build

```bash
make -C submodules/mcu-firmware/applications/cup2023 BOARD=cogip-native
```

#### ARM build

Use the following command to build the ARM version of the firmware:

```bash
make -C submodules/mcu-firmware/applications/cup2023 BOARD=cogip-board-ng
```

### Installation

All tools can be install on the development PC.

!!! note "Python 3.11 or more is required."

To setup a new environment, create a virtual env and install the package in dev mode:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip wheel setuptools
pip install -e .[dev]
```

!!! note "The `dev` optional dependencies include packages used to run Monitor and emulate COGIP tools on the development platform."

### Linting and Formatting

While installing the `dev` environment, `ruff` and `pre-commit` package have been installed.

To run `ruff` manually, just run:

```bash
ruff check [--fix]
ruff format
```

To enable pre-commit hooks prevent committing code not respecting linting and formatting rules, run:

```bash
pre-commit install
```

### Packaging

To build a source distribution package, use:

```bash
python setup.py sdist
```

This will produce `dist/cogip-tools-1.0.0.tar.gz`.

This package can be copied to the Raspberry Pi and installed to deploy the Python tools:

```bash
pip install cogip-tools-1.0.0.tar.gz
```

## Docker Method

### Docker Installation

See [Docker installation instructions](https://docs.docker.com/engine/install/).

### X Server

The `Monitor` is working with X11 but does not behave correctly with Wayland.

To allow the `Monitor` process running in a Docker container to access the X Server running on the host,
you need to run the following command in a terminal:

`$ xhost +local:`

### Configuration

The configuration of the tools is done by setting environment variables in the `.env` file.

All variables supported by the tools are forwarded inside Docker containers.

### Compose Profiles

Several profiles are defined to select which containers to run:

- `beacon`: for the beacon container
- `robotX`: for robot X containers (1 <= X <= 4)
- `monitorX`: for `Monitor` container of robot X (1 <= X <= 4)

Profiles are set in the `.env` file:

`COMPOSE_PROFILES=beacon,robot1,robot2`

### Build Images

Build Docker images:

`docker compose build`

### Run All Tools

Start the Compose stack:

`docker compose up`

### Dashboards Access

The `Beacon Dashboard` (if enabled in `.env`) is accessible using a web browser at `http://localhost:8080`.

The `Dashboard` for robot X (if enabled in `.env`) is accessible using a web browser at `http://localhost:808X`.

### Running Monitor

Instead of running `Monitor` from the Compose stack, it can be launched for robot X (if enabled in `.env`) with:

```bash
cogip-monitor http://localhost:809X
```

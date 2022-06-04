# Raspberry Pi OS Customization

The [raspios](raspios/) directory provides a series of scripts to build and flash
a custom Raspberry Pi OS image running COGIP tools (`Copilot` and `Robotcam`) on the Pi 4 embedded in the robot.

It works by creating a Docker image based on Raspberry Pi OS Lite, use Dockerfiles
to install/configure/remove softwares and services, extract and build the customized image,
and flash it on a SDCard.

## Requirements

 - Docker

See [Docker installation instructions](https://docs.docker.com/engine/install/).

 - ARM Emulation

```
$ sudo apt-get docker install qemu binfmt-support qemu-user-static zerofree
$ docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

## Configuration

Configuration is done by setting required variable in `.env` file in working directory.

Existing variables and example values:

```
IP_ADDRESS=192.168.1.12
GATEWAY=192.168.1.1
WLAN_SSID=My_SSI
WLAN_PSK=<ssi_password>
SDCARD_DEV=/dev/sdc
```

## Stage 0

First stage builds a docker image from original Raspios image.

```
$ ./stage0_base_image.sh
```

## Stage 1

Build a customized docker image:
 - install required Debian and Python packages
 - configure required services
 - install COGIP tools

```
$ ./stage1_customize_image.sh
```

## Stage 1b (under development)

This stage is optional and allow to build a custom kernel image.
It is not working yet so not documented.

## Stage 2

Create the custom filesystem image.

```
$ ./stage2_create_image.sh
```

## Stage 3

Flash the filesystem image on SDCard.

```
$ ./stage3_flash_image.sh
```

# Beacon Server

The `Beacon Server` tool is running on the Raspberry Pi embedded in the central beacon.

It implements a Socket.IO server connected to the `Beacon Dashboard`.

The Socket.IO server listens on port `8090`.

It also implements Socket.IO clients connected to the Socket.IO server of each robot.

Socket.IO clients consider that robot hostnames are `robot1` to `robotN`, resolved by the DNS server or defined in `/etc/hosts` and their ports are `8090 + robot_id`.

## Run Server

```bash
$ cogip-server-beacon
```

## Parameters

`Beacon Server` default parameters can be modified using command line options or environment variables:

```bash
$ cogip-server --help
Usage: cogip-server [OPTIONS]

  --max-robots                    Maximum number of robots to detect (from 1 to max)
                                  env var: SERVER_BEACON_MAX_ROBOTS
                                  default: 4; x>=1

  --record-dir PATH               Directory where games will be recorded
                                  env var: SERVER_BEACON_RECORD_DIR
                                  default: /var/tmp/cogip

  -r, --reload                    Reload app on source file changes
                                  env var: COGIP_RELOAD, SERVER_BEACON_RELOAD

  -d, --debug                     Turn on debug messages
                                  env var: COGIP_DEBUG, SERVER_BEACON_DEBUG
```

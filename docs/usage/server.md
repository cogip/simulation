# Server

The `Server` tool is running on the Raspberry Pi embedded in the central beacon.

It implements a Socket.IO server on which all other tools from robot and centra beacon
are connected on their own namespace.
This server is only used to redirect messages from a tool to another.

It also runs a web server to provide monitoring on any devices (PC, smartphones)
connected to the same network.

## Run Server

```bash
$ cogip-server
```

## Parameters

`Server` default parameters can be modified using command line options or environment variables:

```bash
$ cogip-server --help
Usage: cogip-server [OPTIONS]

  -p, --port INTEGER RANGE        Socket.IO/Web server port
                                  env var: SERVER_PORT
                                  default: 8080; 8000<=x<=8999

  --record-dir PATH               Directory where games will be recorded
                                  env var: SERVER_RECORD_DIR
                                  default: /var/tmp/cogip

  -r, --reload                    Reload app on source file changes
                                  env var: COGIP_RELOAD, PLANNER_RELOAD

  -d, --debug                     Turn on debug messages
                                  env var: COGIP_DEBUG, PLANNER_DEBUG
```

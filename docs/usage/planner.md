# Planner

The `Planner` tool is running on the Raspberry Pi embedded in the central beacon.

It is in charge computing the strategy and giving orders to the robot during the game.

It communicates on the `/planner` namespace of the SocketIO server.

## Data Flow

![Planner Data Flow](../img/cogip-planner.svg)

## Run Planner

```bash
$ cogip-planner
```

## Parameters

`Planner` default parameters can be modified using command line options or environment variables:

```bash
$ cogip-planner --help
Usage: cogip-planner [OPTIONS]

Options:
  --server-url TEXT               Server URL
                                  env var: COGIP_SERVER_URL
                                  default: http://localhost:8080

  -r, --reload                    Reload app on source file changes
                                  env var: COGIP_RELOAD, PLANNER_RELOAD

  -d, --debug                     Turn on debug messages
                                  env var: COGIP_DEBUG, PLANNER_DEBUG
```

# Detector

The `Detector` tool is running on the Raspberry Pi embedded in the robot.

It communicates on the `/detector` namespace of the SocketIO server
running on the central beacon over Wifi.

It builds dynamic obstacles used by `Monitor`/`Dashboards` for display
and by `mcu-firmware` to compute avoidance path.

`Detector` can operate in monitoring or emulation mode.

### Monitoring Mode

Read data from lidar connected on a serial port of the Raspberry Pi.
This is the default mode when a Lidar is connected, since the YDLidar SDK automatically
detects the serial port to use.

### Emulation Mode

Ask the `Monitor` to emulate the Lidar wich sends its data through the SocketIO server.
The emulation mode is enabled if no Lidar is detected at startup.
In case of a false detection, use the `--emulation` option.

## Data Flow

![Detector Data Flow](../img/cogip-detector.svg)

## Run Detector

```bash
$ cogip-detector
```

## Parameters

`Detector` default parameters can be modified using command line options or environment variables:

```
$ cogip-detector --help
Usage: cogip-detector [OPTIONS]

Options:
  --server-url TEXT               Server URL
                                  env var: COGIP_SERVER_URL
                                  default: http://localhost:8080

  --min-distance INTEGER          Minimum distance to detect an obstacle
                                  env var: DETECTOR_MIN_DISTANCE
                                  default: 150

  --max-distance INTEGER          Maximum distance to detect an obstacle
                                  env var: DETECTOR_MAX_DISTANCE
                                  default: 2500

  --obstacle-radius INTEGER       Radius of a dynamic obstacle
                                  env var: DETECTOR_OBSTACLE_RADIUS
                                  default: 500

  --obstacle-bb-margin FLOAT      Obstacle bounding box margin in percent of the radius
                                  env var: DETECTOR_OBSTACLE_BB_MARGIN
                                  default: 0.2

  --obstacle-bb-vertices INTEGER  Number of obstacle bounding box vertices
                                  env var: DETECTOR_OBSTACLE_BB_VERTICES
                                  default: 6

  --beacon-radius INTEGER         Radius of the opponent beacon support
                                  (a cylinder of 70mm diameter to a cube of 100mm width)
                                  env var: DETECTOR_OBSTACLE_RADIUS
                                  default: 35

  --refresh-interval FLOAT        Interval between each update of the obstacle list (in seconds)
                                  env var: DETECTOR_REFRESH_INTERVAL
                                  default: 0.2

  -e, --emulation                 Force emulation mode.
                                  env var: DETECTOR_EMULATION

  -r, --reload                    Reload app on source file changes.
                                  env var: COGIP_RELOAD, DETECTOR_RELOAD

  -d, --debug                     Turn on debug messages.
                                  env var: COGIP_DEBUG, DETECTOR_DEBUG
```

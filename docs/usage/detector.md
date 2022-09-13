# Detector

The `Detector` tool is running on a Raspberry Pi embedded in the robot.
It is connected to the `Copilot` SocketIO server.
It builds dynamic obstacles, sends to then to the `Copilot`, which forward
them to `Monitor`/`Dashboards` for display and to `mcu-firmware` to
compute avoidance path.

`Detector` can operate in two modes:

### Monitoring Mode

Read data from lidar connected on a serial port of the Raspberry Pi.

### Emulation Mode

Tell the `Monitor` to emulate the Lidar and send its data to the `Copilot`
which forward them to `Copilot`.

## Run Detector

```bash
$ cogip-detector
```

## Parameters

`Detector` default parameters can be modified using command line options
or environment variables:

```
$ cogip-detector --help
Usage: cogip-detector [OPTIONS]

Options:
  --uart-port TEXT                Serial port connected to the Lidar  [env
                                  var: DETECTOR_UART_PORT]
  --uart-speed INTEGER            Baud rate  [env var: DETECTOR_UART_SPEED;
                                  default: 230400]
  --copilot-url TEXT              Copilot URL  [env var: DETECTOR_COPILOT_URL;
                                  default: http://localhost:8080]
  --min-distance INTEGER          Minimum distance to detect an obstacle  [env
                                  var: DETECTOR_MIN_DISTANCE; default: 150]
  --max-distance INTEGER          Maximum distance to detect an obstacle  [env
                                  var: DETECTOR_MAX_DISTANCE; default: 1200]
  --lidar-min-intensity INTEGER   Minimum intensity required to validate a
                                  Lidar distance  [env var:
                                  DETECTOR_LIDAR_MIN_INTENSITY; default: 1000]
  --obstacle-radius INTEGER       Radius of a dynamic obstacle  [env var:
                                  DETECTOR_OBSTACLE_RADIUS; default: 500]
  --obstacle-bb-margin FLOAT      Obstacle bounding box margin in percent of
                                  the radius  [env var:
                                  DETECTOR_OBSTACLE_BB_MARGIN; default: 0.2]
  --obstacle-bb-vertices INTEGER  Number of obstacle bounding box vertices
                                  [env var: DETECTOR_OBSTACLE_BB_VERTICES;
                                  default: 6]
  --beacon-radius INTEGER         Radius of the opponent beacon support (a
                                  cylinder of 70mm diameter to a cube of 100mm
                                  width)  [env var: DETECTOR_OBSTACLE_RADIUS;
                                  default: 35]
  --refresh-interval FLOAT        Interval between each update of the obstacle
                                  list (in seconds)  [env var:
                                  DETECTOR_REFRESH_INTERVAL; default: 0.1]
  -d, --debug                     Turn on debug messages.  [env var:
                                  DETECTOR_DEBUG]
```
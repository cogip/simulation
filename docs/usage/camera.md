# Camera

The `Camera` tool provides different commands to get information about cameras,
calibrate them and detect Aruco tags.

Use `--help` argument to show available commands:

```bash
$ cogip-camera --help
Usage: cogip-camera [OPTIONS] COMMAND [ARGS]...

Options:
  -d, --debug           Turn on debug messages
                        env var: COGIP_DEBUG, CAMERA_DEBUG

  --help                Show this message and exit.

Commands:
  info       Get properties of connected cameras
```

## Info Command

Display properties of connected cameras.

If a camera name is provided, only display properties of this camera
and preview its video stream.
Codec, width and height arguments apply only in this context.


```bash
$ cogip-camera info --help
Usage: cogip-camera info [OPTIONS]

  Get properties of connected cameras

Options:
  --camera-name [hbv|sonix]   Name of the camera (all if not specified)
                              env var: CAMERA_NAME

  --camera-codec [mjpg|yuyv]  Camera video codec
                              env var: CAMERA_CODEC
                              default: yuyv

  --camera-width INTEGER      Camera frame width
                              env var: CAMERA_WIDTH
                              default: 640

  --camera-height INTEGER     Camera frame height
                              env var: CAMERA_HEIGHT
                              default: 480

  --help                      Show this message and exit.
```

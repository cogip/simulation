# RobotCam

The `RobotCam` tool is running on the Raspberry Pi embedded in the robot.

It communicates on the `/robotcam` namespace of the SocketIO server
running on the central beacon over Wifi.

It handles the robot camera, detect game elements using Aruco markers and stream the video to a web server.

## Run RobotCam

```bash
$ cogip-robocam
```

## Parameters

RobotCam default parameters can be modified using environment variables.
All variables can be defined in the `.env` file.

Example of `.env` file with all default values:

```bash
# Server URL
COGIP_SERVER_URL="http://localhost:8080"

# Robot ID
ROBOTCAM_ID=1

# Camera device
ROBOTCAM_CAMERA_DEVICE="/dev/v4l/by-id/usb-HBV_HD_CAMERA_HBV_HD_CAMERA-video-index0"

# Camera frame width
ROBOTCAM_CAMERA_WIDTH=640

# Camera frame height
ROBOTCAM_CAMERA_HEIGHT=480

# Camera video codec
ROBOTCAM_CAMERA_CODEC="yuyv"

# Camera intrinsics parameters
ROBOTCAM_CAMERA_PARAMS="[...]/data/coefs-camera-hbv-640x480-yuyv.json"

# Number of uvicorn workers (ignored if launched by gunicorn)
ROBOTCAM_NB_WORKERS=1

# Size of the shared memory storing the last frame to stream on server
# (size for a frame in BMP format, black and white, 640x480 pixels)
ROBOTCAM_FRAME_SIZE=308316
```

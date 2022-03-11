# RobotCam

The RobotCam tool is running on a Raspberry Pi embedded in the robot.
It handles the robot camera, detect samples using Aruco markers and stream the video to a web server.
It is connected to the `Copilot` SocketIO server to send detected samples.

## Run RobotCam

```bash
$ cogip-robocam
```

## Parameters

RobotCam default parameters can be modified using environment variables.
All variables can be defined in the `.env` file.

Example of `.env` file with all default values:

```bash
# Web server port
ROBOTCAM_SERVER_PORT=8081

# Copilot URL
ROBOTCAM_COPILOT_URL="http://localhost:8080"

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
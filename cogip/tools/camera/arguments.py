from pathlib import Path

from cogip.utils.argenum import ArgEnum


class VideoCodec(ArgEnum):
    """Video codecs supported by our cameras"""
    mjpg = "MJPG"
    yuyv = "YUYV"


class CameraName(ArgEnum):
    """Supported cameras"""
    hbv = Path("/dev/v4l/by-id/usb-HBV_HD_CAMERA_HBV_HD_CAMERA-video-index0")
    sonix = Path("/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0")

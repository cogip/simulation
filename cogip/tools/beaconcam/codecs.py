from enum import Enum


class VideoCodec(str, Enum):
    """Video codecs supported by our cameras"""
    mjpg = "MJPG"
    yuyv = "YUYV"

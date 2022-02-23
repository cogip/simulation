from pathlib import Path

from pydantic import BaseSettings, Field, FilePath

from .codecs import VideoCodec


class Settings(BaseSettings):
    server_port: int = Field(
        default=8081,
        description="Web server port"
    )
    copilot_url: str = Field(
        "http://localhost:8080",
        description="Copilot URL"
    )
    camera_device: Path = Field(
        default="/dev/v4l/by-id/usb-HBV_HD_CAMERA_HBV_HD_CAMERA-video-index0",
        description="Camera device"
    )
    camera_width: int = Field(
        default=640,
        description="Camera frame width"
    )
    camera_height: int = Field(
        default=480,
        description="Camera frame height"
    )
    camera_codec: VideoCodec = Field(
        default=VideoCodec.yuyv,
        description="Camera video codec"
    )
    camera_params: FilePath = Field(
        default=Path(__file__).parent / "data" / "coefs-camera-hbv-640x480-yuyv.json",
        description="Camera intrinsics parameters"
    )
    nb_workers: int = Field(
        default=1,
        description="Number of uvicorn workers (ignored if launched by gunicorn)"
    )
    frame_size: int = Field(
        default=308316,  # size for a frame in BMP format, black and white, 640x480 pixels.
        description="Size of the shared memory storing the last frame to stream on server"
    )

    class Config:
        env_prefix = 'robotcam_'

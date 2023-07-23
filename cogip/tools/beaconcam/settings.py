from pathlib import Path

from pydantic import AnyHttpUrl, BaseSettings, Field, FilePath

from .codecs import VideoCodec


class Settings(BaseSettings):
    server_url: AnyHttpUrl = Field(
        "http://localhost:8080",
        description="Server URL"
    )
    camera_device: Path = Field(
        default="/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0",
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
        default=Path(__file__).parent / "data" / "coefs-camera-sonix-640x480-yuyv-8x13.json",
        description="Camera intrinsics parameters"
    )
    nb_workers: int = Field(
        default=1,
        description="Number of uvicorn workers (ignored if launched by gunicorn)"
    )

    class Config:
        env_prefix = 'beaconcam_'
        fields = {
            'server_url': {
                'env': 'cogip_server_url'
            }
        }
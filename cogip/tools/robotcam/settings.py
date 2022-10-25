from pathlib import Path

from pydantic import AnyHttpUrl, BaseSettings, Field, FilePath

from .codecs import VideoCodec


class Settings(BaseSettings):
    server_url: AnyHttpUrl = Field(
        "http://localhost:8080",
        description="Server URL"
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
    calibration: bool = Field(
        default=False,
        description="Using sample calibration board, display distance between tags"
    )

    class Config:
        env_prefix = 'robotcam_'
        fields = {
            'id': {
                'env': ["robot_id", "robotcam_id"]
            },
            'server_url': {
                'env': 'cogip_server_url'
            }
        }

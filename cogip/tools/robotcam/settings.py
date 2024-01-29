from pydantic import AnyHttpUrl, Field, FilePath
from pydantic_settings import BaseSettings, SettingsConfigDict

from cogip.tools.camera.arguments import (
    CameraName,
    CameraNameLiteral,
    VideoCodec,
    VideoCodecLiteral,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='robotcam_', use_enum_values=False)

    id: int = Field(
        default=1,
        ge=1,
        help="Robot ID",
        alias="robot_id"
    )
    socketio_server_url: AnyHttpUrl = Field(
        "http://localhost:8090",
        description="Socket.IO Server URL",
        alias="cogip_socketio_server_url"
    )
    camera_name: CameraNameLiteral = Field(
        default=CameraName.hbv.name,
        description="Name of the camera",
        validate_default=True
    )
    camera_width: int = Field(
        default=640,
        description="Camera frame width"
    )
    camera_height: int = Field(
        default=480,
        description="Camera frame height"
    )
    camera_codec: VideoCodecLiteral = Field(
        default=VideoCodec.yuyv.name,
        description="Camera video codec",
        validate_default=True
    )
    camera_intrinsic_params: FilePath | None = Field(
        default=None,
        description="Camera intrinsic parameters"
    )
    camera_extrinsic_params: FilePath | None = Field(
        default=None,
        description="Camera extrinsic parameters"
    )
    nb_workers: int = Field(
        default=1,
        description="Number of uvicorn workers (ignored if launched by gunicorn)"
    )

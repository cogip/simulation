from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    server_port: int = Field(
        default=8080,
        description="Socket.IO/Web server port"
    )
    serial_port: Path = Field(
        default="/dev/ttyUSB0",
        description="Serial port connected to STM32 device"
    )
    serial_baud: int = Field(
        default=230400,
        description="Baud rate"
    )

    class Config:
        env_prefix = 'copilot_'

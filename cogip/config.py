from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    This class gives default values for different parameters.
    These parameters can be also set as environment variables or in the `.env` file.

    Attributes:
        default_uart: Serial port used by default (default: "/tmp/ptsCOGIP")
        native_binary: `mcu_firmware` compiled in native mode
    """

    default_uart: str = "/tmp/ptsCOGIP"
    native_binary: Path = "submodules/mcu-firmware/applications/cup2019/bin/cogip-native/cortex.elf"


settings = Settings()

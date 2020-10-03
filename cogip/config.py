from pydantic import BaseSettings, FilePath


class Settings(BaseSettings):
    """
    This class gives default values for different parameters.
    These parameters can be also set as environment variables or in the `.env` file.

    Attributes:
        default_uart: Serial port used by default
            (default: "/tmp/ptsCOGIP")
        table_filename: Name of the file containing the table asset
            (default: "assets/table2019.dae")
        robot_filename: Name of the file containing the robot asset
            (default: "assets/robot2019.dae")
        native_binary: `mcu_firmware` compiled in native mode
    """

    default_uart: str = "/tmp/ptsCOGIP"
    table_filename: FilePath = "assets/table2019.dae"
    robot_filename: FilePath = "assets/robot2019.dae"
    native_binary: FilePath = "submodules/mcu-firmware/applications/cogip2019-cortex/bin/cogip2019-cortex-native/cortex.elf"


settings = Settings()

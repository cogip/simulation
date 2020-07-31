from pydantic import BaseSettings, FilePath


class Config(BaseSettings):
    """Config class

    This class give default values for different parameters.
    These parameters can be also set as environment variables or in the `.env` file.
    """

    default_uart: str = "/tmp/ptsCOGIP"
    table_filename: FilePath = "../models/table2019.dae"
    robot_filename: FilePath = "../models/robot2019_simu.dae"
    native_binary: FilePath = "submodules/mcu-firmware/applications/cogip2019-cortex/bin/cogip2019-cortex-native/cortex.elf"


settings = Config()

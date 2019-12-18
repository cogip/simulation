import os

class Config(object):
    """Config class

    This class give default values for different parameters.
    These parameters can be also set as environment variables or in the `.env` file. 
    """

    DEFAULT_UART = os.environ.get("DEFAULT_UART") or "/tmp/ptsCOGIP"
    TABLE_FILENAME = os.environ.get("TABLE_FILENAME") or "../models/table2019.iges"
    ROBOT_FILENAME = os.environ.get("ROBOT_FILENAME") or "../models/robot2019_simu.step"
    NATIVE_BINARY = os.environ.get("SIMULATION_BINARY") or "../platforms/cogip2019-cortex-simulation/bin/cogip2019-cortex-native/cortex-simulation.elf"
    # NATIVE_BINARY = os.environ.get("SIMULATION_BINARY") or "/home/eric/cogip/mcu-firmware-ygl-pid-calib-next/platforms/cogip2019-cortex-simulation/bin/cogip2019-cortex-native/cortex-simulation.elf"

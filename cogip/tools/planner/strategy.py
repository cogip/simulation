from enum import IntEnum


class Strategy(IntEnum):
    """
    Enum for available strategies.
    """

    Approval = 0
    Game = 1
    BackAndForth = 2
    AngularSpeedTest = 3
    LinearSpeedTest = 4
    Training = 5
    CameraCalibration = 6
    SolarPanel = 7

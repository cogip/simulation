from enum import IntEnum, auto


class Strategy(IntEnum):
    """
    Enum for available strategies.
    """

    Approval = auto()
    Game = auto()
    BackAndForth = auto()
    AngularSpeedTest = auto()
    LinearSpeedTest = auto()
    AngularPositionTest = auto()
    LinearPositionTest = auto()
    Training = auto()
    CameraCalibration = auto()
    SolarPanel = auto()

from enum import IntEnum, auto


class Strategy(IntEnum):
    """
    Enum for available strategies.
    """

    GameGripFirst = auto()
    GameSolarFirst = auto()
    BackAndForth = auto()
    AngularSpeedTest = auto()
    LinearSpeedTest = auto()
    AngularPositionTest = auto()
    LinearPositionTest = auto()
    CameraCalibration = auto()
    SolarPanel = auto()
    TestAlign = auto()
    TestGrip = auto()
    TestPotCapture = auto()
    TestSolarPanels = auto()
    TestDropoff = auto()
    TestPlanter = auto()

from enum import IntEnum, auto


class StartPosition(IntEnum):
    """
    Enum for available start positions.
    """

    Top = auto()
    Bottom = auto()
    Opposite = auto()
    PAMI2 = auto()
    PAMI3 = auto()
    PAMI4 = auto()
    PAMI2_TRAINING = auto()
    PAMI3_TRAINING = auto()
    PAMI4_TRAINING = auto()
    Center = auto()

from enum import IntEnum


class ControllerEnum(IntEnum):
    QUADPID = 0
    ANGULAR_SPEED_TEST = 1
    LINEAR_SPEED_TEST = 2
    LINEAR_POSE_DISABLED = 3

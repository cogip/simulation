"""
This module contains all data models used in the monitor.

The models are based on [Pydantic](https://pydantic-docs.helpmanual.io/) models,
allowing them to be loaded from/exported to JSON strings/files.
All values are automatically verified and converted to the expected data type,
an exception being raised if impossible.
"""

from enum import auto, IntEnum
from typing import List, Union

from pydantic import BaseModel

from cogip.tools.copilot.messages import PB_PathPose


class MenuEntry(BaseModel):
    """
    Represents one entry in a firmware's shell menu

    Attributes:
        cmd: Command name
        desc: Description of the command

    Examples:
        The following line shows how to initialize this class from a JSON
        string received on the serial port:
        ```py
        MenuEntry.parse_raw("{\\"cmd\\": \\"_state\\", \\"desc\\": \\"Print current state\\"}")
        ```
    """
    cmd: str
    desc: str


class ShellMenu(BaseModel):
    """
    Represents a firmware's shell menu.

    Attributes:
        name: Name of the menu
        entries: List of the menu entries

    Examples:
        The following line shows how to initialize this class from a JSON
        string received on the serial port:
        ```py
        ShellMenu.parse_raw(
            "{\\"name\\": \\"planner\\","
            " \\"entries\\": ["
            "    {\\"cmd\\": \\"_help_json\\", \\"desc\\": \\"Display available commands in JSON format\\"},"
            "    {\\"cmd\\": \\"_state\\", \\"desc\\": \\"Print current state\\"}
            "]}"
        )
        ```
    """
    name: str
    entries: List[MenuEntry]


class Vertex(BaseModel):
    """
    Represents a point in 2D/3D coordinates.

    Attributes:
        x: X position
        y: Y position
        z: Z position (optional)
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class Pose(Vertex):
    """
    A position of the robot.

    Attributes:
        x: X position
        y: Y position
        O: Rotation
    """
    O: float = 0.0


class Speed(BaseModel):
    """
    A speed value.

    Attributes:
        distance: Linear speed
        angle: Angular speed
    """
    distance: float = 0.0
    angle: float = 0.0


class SpeedEnum(IntEnum):
    """
    Speed levels.
    In mcu-firmware, the speeds (linear and angular) are float-point values,
    but they can take only 3 values: low, normal and max speed. These values
    depend on the platform, so on the Raspberry side, we only need to define
    the speed levels instead of the real values.

    Attributes:
        LOW:
        NORMAL:
        MAX:
    """
    LOW = 0
    NORMAL = 1
    MAX = 2


class PathPose(Pose):
    """
        Class representing a position in a path.

        Attributes:
            x: X coordinate
            y: Y coordinate
            O: 0-orientation
            max_speed_linear: max speed linear
            max_speed_angular: max speed angular
            allow_reverse: reverse mode
    """
    max_speed_linear: SpeedEnum = SpeedEnum.NORMAL
    max_speed_angular: SpeedEnum = SpeedEnum.NORMAL
    allow_reverse: bool = True

    @property
    def pose(self) -> Pose:
        return Pose(**self.dict())

    def copy_pb(self, pb_path_pose: PB_PathPose) -> None:
        """
        Copy data in a Protobuf message.

        Arguments:
            pb_path_pose: Protobuf message to fill
        """
        pb_path_pose.pose.x = int(self.x)
        pb_path_pose.pose.y = int(self.y)
        pb_path_pose.pose.O = int(self.O)  # noqa
        pb_path_pose.max_speed_linear_enum = self.max_speed_linear
        pb_path_pose.max_speed_angular_enum = self.max_speed_angular
        pb_path_pose.allow_reverse = self.allow_reverse


class DynObstacleRect(BaseModel):
    """
    A dynamic rectangle obstacle created by the robot.

    Attributes:
        x: X coordinate of the obstacle center
        y: Y coordinate of the obstacle center
        angle: Orientation of the obstacle
        length_x: length along X axis
        length_y: length along Y axis
        bb: bounding box
    """
    x: float
    y: float
    angle: float
    length_x: float
    length_y: float
    bb: List[Vertex] = []

    def __hash__(self):
        """
        Hash function to allow this class to be used as a key in a dict.
        """
        return hash((type(self),) + tuple(self.__root__))


class DynRoundObstacle(BaseModel):
    """
    A dynamic round obstacle created by the robot.

    Attributes:
        x: Center X position
        y: Center Y position
        radius: Radius of the obstacle
        bb: bounding box
    """
    x: float
    y: float
    radius: float
    bb: List[Vertex] = []

    def contains(self, point: Vertex) -> bool:
        return (point.x - self.x) * (point.x - self.x) + (point.y - self.y) * (point.y - self.y) <= self.radius ** 2

    def __hash__(self):
        """
        Hash function to allow this class to be used as a key in a dict.
        """
        return hash((type(self),) + tuple(self.__root__))


DynObstacle = Union[DynRoundObstacle, DynObstacleRect]
DynObstacleList = List[DynObstacle]


class RobotState(BaseModel):
    """
    This contains information about robot state,
    like mode, cycle, positions, speed, path and obstacles.
    It is given by the firmware through the serial port.

    Attributes:
        pose_order: Position to reach
        cycle: Current cycle
        speed_current: Current speed
        speed_order: Speed order
        path: Computed path
    """
    pose_current: Pose = Pose()
    pose_order: Pose = Pose()
    cycle: int = 0
    speed_current: Speed = Speed()
    speed_order: Speed = Speed()


class Obstacle(BaseModel):
    """
    Contains the properties of an obstacle added on the table.

    Attributes:
        x: X position
        y: Y position
        rotation: Rotation
        length: Length
        width: Width
        height: Height
        bb: bounding box
    """
    x: int = 0
    y: int = 1000
    rotation: int = 0
    length: int = 200
    width: int = 200
    height: int = 600


ObstacleList = List[Obstacle]


class LogMessage(BaseModel):
    """
    A log received on the serial port.

    Attributes:
        log: message
    """
    log: str


SerialMessage = Union[RobotState, ShellMenu, LogMessage]


class CakeLayerID(IntEnum):
    """
    Enum to identify each sample
    """
    GREEN_FRONT_ICING_BOTTOM = auto()
    GREEN_FRONT_ICING_MIDDLE = auto()
    GREEN_FRONT_ICING_TOP = auto()
    GREEN_FRONT_CREAM_BOTTOM = auto()
    GREEN_FRONT_CREAM_MIDDLE = auto()
    GREEN_FRONT_CREAM_TOP = auto()
    GREEN_FRONT_SPONGE_BOTTOM = auto()
    GREEN_FRONT_SPONGE_MIDDLE = auto()
    GREEN_FRONT_SPONGE_TOP = auto()

    GREEN_BACK_SPONGE_BOTTOM = auto()
    GREEN_BACK_SPONGE_MIDDLE = auto()
    GREEN_BACK_SPONGE_TOP = auto()
    GREEN_BACK_CREAM_BOTTOM = auto()
    GREEN_BACK_CREAM_MIDDLE = auto()
    GREEN_BACK_CREAM_TOP = auto()
    GREEN_BACK_ICING_BOTTOM = auto()
    GREEN_BACK_ICING_MIDDLE = auto()
    GREEN_BACK_ICING_TOP = auto()

    BLUE_FRONT_ICING_BOTTOM = auto()
    BLUE_FRONT_ICING_MIDDLE = auto()
    BLUE_FRONT_ICING_TOP = auto()
    BLUE_FRONT_CREAM_BOTTOM = auto()
    BLUE_FRONT_CREAM_MIDDLE = auto()
    BLUE_FRONT_CREAM_TOP = auto()
    BLUE_FRONT_SPONGE_BOTTOM = auto()
    BLUE_FRONT_SPONGE_MIDDLE = auto()
    BLUE_FRONT_SPONGE_TOP = auto()

    BLUE_BACK_SPONGE_BOTTOM = auto()
    BLUE_BACK_SPONGE_MIDDLE = auto()
    BLUE_BACK_SPONGE_TOP = auto()
    BLUE_BACK_CREAM_BOTTOM = auto()
    BLUE_BACK_CREAM_MIDDLE = auto()
    BLUE_BACK_CREAM_TOP = auto()
    BLUE_BACK_ICING_BOTTOM = auto()
    BLUE_BACK_ICING_MIDDLE = auto()
    BLUE_BACK_ICING_TOP = auto()


class CakeLayerKind(IntEnum):
    """
    Enum for cake layers

    Attributes:
        ICING:
        CREAM:
        SPONGE:
    """
    ICING = auto()
    CREAM = auto()
    SPONGE = auto()


class CakeLayerPos(IntEnum):
    """
    Enum for cake layer positions

    Attributes:
        TOP:
        MIDDLE:
        BOTTOM:
    """
    TOP = auto()
    MIDDLE = auto()
    BOTTOM = auto()


class CakeLayer(BaseModel):
    """
    Contains the properties of a cake layer on the table.

    Attributes:
        id: cake layer id
        x: X coordinate
        y: Y coordinate
        pos: layer position
        kind: layer kind
    """
    id: CakeLayerID
    x: float
    y: float
    pos: CakeLayerPos
    kind: CakeLayerKind


class CherryID(IntEnum):
    """
    Enum to identify each cherry
    """
    FRONT_1 = auto()
    FRONT_2 = auto()
    FRONT_3 = auto()
    FRONT_4 = auto()
    FRONT_5 = auto()
    FRONT_6 = auto()
    FRONT_7 = auto()
    FRONT_8 = auto()
    FRONT_9 = auto()
    FRONT_10 = auto()

    BACK_1 = auto()
    BACK_2 = auto()
    BACK_3 = auto()
    BACK_4 = auto()
    BACK_5 = auto()
    BACK_6 = auto()
    BACK_7 = auto()
    BACK_8 = auto()
    BACK_9 = auto()
    BACK_10 = auto()

    GREEN_1 = auto()
    GREEN_2 = auto()
    GREEN_3 = auto()
    GREEN_4 = auto()
    GREEN_5 = auto()
    GREEN_6 = auto()
    GREEN_7 = auto()
    GREEN_8 = auto()
    GREEN_9 = auto()
    GREEN_10 = auto()

    BLUE_1 = auto()
    BLUE_2 = auto()
    BLUE_3 = auto()
    BLUE_4 = auto()
    BLUE_5 = auto()
    BLUE_6 = auto()
    BLUE_7 = auto()
    BLUE_8 = auto()
    BLUE_9 = auto()
    BLUE_10 = auto()

    ROBOT_1 = auto()
    ROBOT_2 = auto()
    ROBOT_3 = auto()
    ROBOT_4 = auto()
    ROBOT_5 = auto()
    ROBOT_6 = auto()
    ROBOT_7 = auto()
    ROBOT_8 = auto()
    ROBOT_9 = auto()
    ROBOT_10 = auto()

    OPPONENT_1 = auto()
    OPPONENT_2 = auto()
    OPPONENT_3 = auto()
    OPPONENT_4 = auto()
    OPPONENT_5 = auto()
    OPPONENT_6 = auto()
    OPPONENT_7 = auto()
    OPPONENT_8 = auto()
    OPPONENT_9 = auto()
    OPPONENT_10 = auto()


class CherryLocation(IntEnum):
    """
    Enum for cherry locations

    Attributes:
        TOP:
        MIDDLE:
        BOTTOM:
        RACK:
        ROBOT:
        OPPONENT:
        BASKET:
    """
    TOP = auto()
    MIDDLE = auto()
    BOTTOM = auto()
    RACK = auto()
    ROBOT = auto()
    OPPONENT = auto()
    BASKET = auto()

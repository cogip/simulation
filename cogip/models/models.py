"""
This module contains all data models used in the simulator.

The models are based on [Pydantic](https://pydantic-docs.helpmanual.io/) models,
allowing them to be loaded from/exported to JSON strings/files.
All values are automatically verified and converted to the expected data type,
an exception being raised if impossible.
"""

from enum import IntEnum
from typing import List, Optional, Union

from pydantic import BaseModel


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


class CtrlModeEnum(IntEnum):
    """
    Enum containing all internal modes of the robot

    Attributes:
        STOP:
        IDLE:
        BLOCKED:
        RUNNING:
        RUNNING_SPEED:
        PASSTHROUGH:

    """
    STOP = 0,
    IDLE = 1,
    BLOCKED = 2,
    RUNNING = 3,
    RUNNING_SPEED = 4,
    PASSTHROUGH = 5


class Vertex(BaseModel):
    """
    Represents a point in 2D/3D coordinates.

    Attributes:
        x: X position
        y: Y position
        z: Z position (optional)
    """
    x: float
    y: float
    z: float = 0.0

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class Pose(Vertex):
    """
    A position of the robot.

    Attributes:
        x: X position
        y: Y postion
        O: Rotation
    """
    O: float


class Speed(BaseModel):
    """
    A speed value.

    Attributes:
        distance: Linear speed
        angle: Angular speed
    """
    distance: float
    angle: float


class DynObstacleRect(BaseModel):
    """
    A dynamic rectangle obstacle created by the robot.

    Attributes:
        x: X coordinate of the obstacle center
        y: Y coordinate of the obstacle center
        angle: Orientation of the obstacle
        length_x: length along X axis
        length_y: length along Y axis
    """
    x: float
    y: float
    angle: float
    length_x: float
    length_y: float

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
    """
    x: float
    y: float
    radius: float

    def __hash__(self):
        """
        Hash function to allow this class to be used as a key in a dict.
        """
        return hash((type(self),) + tuple(self.__root__))


DynObstacle = Union[DynRoundObstacle, DynObstacleRect]


class DynObstacleList(BaseModel):
    """
    List of dynamic obstacles.

    Attributes:
        __root__: List of dynamic obstacles
    """
    __root__: List[DynObstacle]

    def __hash__(self):
        """
        Hash function to allow this class to be used as a key in a dict.
        """
        return hash((type(self),) + tuple(self.__root__))


class RobotState(BaseModel):
    """
    This contains information about robot state,
    like mode, cycle, positions, speed, path and obstacles.
    It is given by the firmware through the serial port.

    Attributes:
        mode: Current robot mode
        pose_current: Current robot position
        pose_order: Position to reach
        cycle: Current cycle
        speed_current: Current speed
        speed_order: Speed order
        path: Computed path
    """
    mode: CtrlModeEnum
    pose_current: Pose
    pose_order: Pose
    cycle: Optional[int] = None
    speed_current: Optional[Speed] = None
    speed_order: Optional[Speed] = None
    path: List[Vertex] = []
    obstacles: DynObstacleList


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
    """
    x: int = 0
    y: int = 1000
    rotation: int = 0
    length: int = 200
    width: int = 200
    height: int = 600


class ObstacleList(BaseModel):
    """
    List of obstacles.

    Attributes:
        __root__: List of obstacles
    """
    __root__: List[Obstacle]

    def __iter__(self):
        """
        Function a make the class iterable
        """
        return iter(self.__root__)

    def append(self, item):
        """
        Add a obstacle to the list
        """
        self.__root__.append(item)


class LogMessage(BaseModel):
    """
    A log received on the serial port.

    Attributes:
        log: message
    """
    log: str


SerialMessage = Union[RobotState, ShellMenu, LogMessage]

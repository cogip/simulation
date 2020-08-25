from enum import IntEnum
from typing import List

from pydantic import BaseModel


class MenuEntry(BaseModel):
    cmd: str
    desc: str


class ShellMenu(BaseModel):
    name: str
    entries: List[MenuEntry]


class CtrlModeEnum(IntEnum):
    STOP = 0,
    IDLE = 1,
    BLOCKED = 2,
    RUNNING = 3,
    RUNNING_SPEED = 4,
    PASSTHROUGH = 5


class HashableBaseModel(BaseModel):
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class Vertex(BaseModel):
    x: float
    y: float

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))


class PoseCurrent(Vertex):
    mode: CtrlModeEnum
    O: float


class DynObstacle(BaseModel):
    __root__: List[Vertex]

    def __hash__(self):
        return hash((type(self),) + tuple(self.__root__))


class DynObstacleList(BaseModel):
    __root__: List[DynObstacle]

    def __hash__(self):
        return hash((type(self),) + tuple(self.__root__))


class Obstacle(BaseModel):
    x: int = 0,
    y: int = 1000,
    rotation: int = 0,
    length: int = 200,
    width: int = 200,
    height: int = 600


class ObstacleList(BaseModel):
    __root__: List[Obstacle]

    def __iter__(self):
        return iter(self.__root__)

    def append(self, item):
        self.__root__.append(item)

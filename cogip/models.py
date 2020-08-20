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

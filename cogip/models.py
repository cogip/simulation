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


class PoseCurrent(BaseModel):
    mode: CtrlModeEnum
    O: float
    x: float
    y: float

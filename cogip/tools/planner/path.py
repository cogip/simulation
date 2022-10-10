from __future__ import annotations
from typing import List
from pydantic import BaseModel, PrivateAttr

from cogip import models


class Path(BaseModel):
    index: int = 0
    poses: List[models.PathPose]
    play_in_loop: bool = False
    _playing: bool = PrivateAttr(False)

    def pose(self, index: int | None = None) -> models.PathPose | None:
        try:
            return self.poses[index or self.index]
        except IndexError:
            return None

    def reset(self) -> None:
        self.index = 0
        self._playing = False

    def incr(self) -> models.PathPose | None:
        if self.index < len(self.poses) - 1:
            self.index += 1
        elif self.play_in_loop:
            self.reset()
        return self.pose()

    def decr(self) -> models.PathPose | None:
        if self.index > 0:
            self.index -= 1
        elif self.play_in_loop:
            self.index = len(self.poses) - 1
        return self.pose()

    def mirror(self):
        for pose in self.poses:
            pose.mirror()

    @property
    def playing(self) -> bool:
        return self._playing

    def play(self):
        self._playing = True

    def stop(self):
        self._playing = False


path = Path(
    index=0,
    poses=[
        models.PathPose(
            x=225, y=1000-225, O=0,
            max_speed_linear=models.SpeedEnum.MAX,
            max_speed_angular=models.SpeedEnum.MAX,
        ),
        models.PathPose(
            x=450+125+200+125+225, y=-1000+225, O=0,
            max_speed_linear=models.SpeedEnum.MAX,
            max_speed_angular=models.SpeedEnum.MAX,
        ),
        models.PathPose(
            x=3000-225, y=-1000+225, O=90,
            max_speed_linear=models.SpeedEnum.MAX,
            max_speed_angular=models.SpeedEnum.MAX,
        ),
        models.PathPose(
            x=3000-225, y=50+225, O=90,
            max_speed_linear=models.SpeedEnum.MAX,
            max_speed_angular=models.SpeedEnum.MAX,
        ),
        models.PathPose(
            x=3000-(450+125+200+125+225), y=1000-225, O=180,
            max_speed_linear=models.SpeedEnum.MAX,
            max_speed_angular=models.SpeedEnum.MAX,
        ),
        models.PathPose(
            x=225, y=1000-225, O=0,
            max_speed_linear=models.SpeedEnum.MAX,
            max_speed_angular=models.SpeedEnum.MAX,
        )
    ]
)

from functools import partial
from typing import TYPE_CHECKING

from cogip.models.models import SpeedEnum
from ..pose import Pose
from .actions import Action, Actions

if TYPE_CHECKING:
    from ..planner import Planner


class BackAndForthAction(Action):
    """
    Example action that generate its poses depending of the robot's pose
    at the beginning of the action.
    The robot will go from the current position to its opposite position in loop.
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("BackAnForth action", planner, actions)
        self.before_action_func = self.compute_poses

    async def compute_poses(self) -> None:
        x = self.planner.pose_current.x
        y = self.game_context.table.y_min + self.game_context.table.y_max - self.planner.pose_current.y
        angle = -self.planner.pose_current.O
        pose1 = Pose(
            x=x,
            y=y,
            O=angle,
            max_speed_linear=SpeedEnum.NORMAL,
            max_speed_angular=SpeedEnum.NORMAL,
        )
        pose2 = Pose(**self.planner.pose_current.model_dump())
        pose1.after_pose_func = partial(self.append_pose, pose1)
        pose2.after_pose_func = partial(self.append_pose, pose2)
        self.poses.append(pose1)
        self.poses.append(pose2)

    async def append_pose(self, pose: Pose) -> None:
        self.poses.append(pose)

    def weight(self) -> float:
        return 1000000.0


class BackAndForthActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(BackAndForthAction(planner, self))
        self.append(BackAndForthAction(planner, self))
        self.append(BackAndForthAction(planner, self))
        self.append(BackAndForthAction(planner, self))

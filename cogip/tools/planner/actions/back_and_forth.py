from functools import partial
from typing import TYPE_CHECKING

from cogip.models.models import SpeedEnum
from ..pose import Pose
from .actions import Action, Actions

if TYPE_CHECKING:
    from ..planner import Planner
    from ..robot import Robot


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
        x = self.game_context.table.x_min + self.game_context.table.x_max - self.robot.pose_current.x
        y = self.game_context.table.y_min + self.game_context.table.y_max - self.robot.pose_current.y
        angle = self.robot.pose_current.O
        if angle < 0:
            angle = self.robot.pose_current.O + 180
        else:
            angle = self.robot.pose_current.O - 180
        pose1 = Pose(
            x=x, y=y, O=angle,
            max_speed_linear=SpeedEnum.NORMAL, max_speed_angular=SpeedEnum.NORMAL
        )
        pose2 = Pose(**self.robot.pose_current.dict())
        pose1.after_pose_func = partial(self.append_pose, pose1)
        pose2.after_pose_func = partial(self.append_pose, pose2)
        self.poses.append(pose1)
        self.poses.append(pose2)

    async def append_pose(self, pose: Pose) -> None:
        self.poses.append(pose)

    def weight(self, robot: "Robot") -> float:
        return 1000000.0


class BackAndForthActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(BackAndForthAction(planner, self))
        self.append(BackAndForthAction(planner, self))
        self.append(BackAndForthAction(planner, self))
        self.append(BackAndForthAction(planner, self))

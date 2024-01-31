from typing import TYPE_CHECKING

from ..pose import Pose
from .actions import Action, Actions

if TYPE_CHECKING:
    from ..planner import Planner
    from ..robot import Robot


class SpeedTestAction(Action):
    """
    Dummy action for pid calibration.
    Same dummy pose in loop.
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("Pid calibration action", planner, actions)
        self.pose = Pose()
        self.pose.after_pose_func = self.after_pose
        self.poses = [self.pose]

    def weight(self, robot: "Robot") -> float:
        return 1000000.0

    async def after_pose(self):
        self.poses.append(self.pose)


class SpeedTestActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(SpeedTestAction(planner, self))

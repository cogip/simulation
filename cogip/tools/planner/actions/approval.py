from typing import TYPE_CHECKING

from ..pose import AdaptedPose
from .actions import Action, Actions

if TYPE_CHECKING:
    from ..planner import Planner


class ApprovalAction(Action):
    """
    Example of the simple action with a pose that calls a function of the action itself
    to reset the list of poses.
    The robot will go from a point to another in loop.
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("Approval action", planner, actions)
        self.default_poses = [
            AdaptedPose(
                x=self.game_context.table.x_min + 300,
                y=-(self.game_context.table.y_max + self.game_context.table.y_min) / 2 - 200,
                O=0,
                max_speed_linear=66,
                max_speed_angular=66,
            ),
            AdaptedPose(
                x=self.game_context.table.x_max - 300,
                y=-(self.game_context.table.y_max + self.game_context.table.y_min) / 2 - 200,
                O=180,
                max_speed_linear=66,
                max_speed_angular=66,
                after_pose_func=self.areset,
            ),
        ]
        self.reset()

    async def areset(self):
        self.reset()

    def reset(self):
        self.poses = [pose.model_copy() for pose in self.default_poses]

    def weight(self) -> float:
        return 1000000.0


class ApprovalActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(ApprovalAction(planner, self))

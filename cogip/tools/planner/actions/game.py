import math
from typing import TYPE_CHECKING

from cogip.models import models
from .. import actuators
from ..camp import Camp
from ..pose import Pose
from .actions import Action, Actions, WaitAction

if TYPE_CHECKING:
    from ..planner import Planner


class ParkingAction(Action):
    def __init__(self, planner: "Planner", actions: Actions, pose: models.Pose):
        super().__init__(f"Parking action at ({int(pose.x)}, {int(pose.y)})", planner, actions, interruptable=False)
        self.before_action_func = self.before_action
        self.after_action_func = self.after_action
        self.actions_backup: Actions = []

        self.pose = Pose(**pose.model_dump())
        self.poses = [self.pose]

    def weight(self) -> float:
        if self.game_context.countdown > 15:
            return 0

        dist = math.dist((self.pose.x, self.pose.y), (self.planner.pose_current.x, self.planner.pose_current.y))
        # Max distance is 3600, calculate the ratio between 0 and 1000
        dist = (3600 - dist) / 3600 * 1000

        return 100000 + dist

    async def before_action(self):
        await actuators.central_arm_up(self.planner)
        await actuators.left_arm_up(self.planner)
        await actuators.right_arm_up(self.planner)

        # Backup actions if the action is recycled
        self.actions_backup = self.actions[:]

        # Clear remaining actions
        self.actions.clear()

    async def after_action(self):
        await self.planner.sio_ns.emit("robot_end")

    async def recycle(self):
        if self.actions_backup:
            self.actions = self.actions_backup[:]
            self.actions_backup.clear()
        self.recycled = True


class GameActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(WaitAction(planner, self))

        if Camp().color == Camp.Colors.blue:
            self.append(ParkingAction(planner, self, models.Pose(x=700, y=450, O=180)))
        else:
            self.append(ParkingAction(planner, self, models.Pose(x=700, y=-450, O=180)))

        self.planner.start_position = 1

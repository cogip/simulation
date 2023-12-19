import math
from typing import TYPE_CHECKING

# from cogip.models import actuators
from cogip.models import models
from .. import actuators
from ..camp import Camp
from ..pose import Pose
from .actions import Action, Actions, WaitAction

if TYPE_CHECKING:
    from ..planner import Planner
    from ..robot import Robot


class ParkingAction(Action):
    nb_robots: int = 0

    def __init__(
            self,
            planner: "Planner", actions: Actions,
            pose: models.Pose):
        super().__init__(f"Parking action at ({int(pose.x)}, {int(pose.y)})", planner, actions)
        self.before_action_func = self.before_action
        self.after_action_func = self.after_action

        self.pose = Pose(
            **pose.dict()
        )
        self.poses = [self.pose]

    def weight(self, robot: "Robot") -> float:
        if self.game_context.countdown > 15:
            return 0

        dist = math.dist((self.pose.x, self.pose.y), (robot.pose_current.x, robot.pose_current.y))
        # Max distance is 3600, calculate the ratio between 0 and 1000
        dist = (3600 - dist) / 3600 * 1000

        return 100000 + dist

    async def before_action(self):
        ParkingAction.nb_robots += 1
        await actuators.central_arm_up(self.robot.robot_id, self.planner)
        await actuators.cherry_arm_up(self.robot.robot_id, self.planner)
        await actuators.left_arm_up(self.robot.robot_id, self.planner)
        await actuators.right_arm_up(self.robot.robot_id, self.planner)

        if ParkingAction.nb_robots == len(self.planner._robots):
            self.actions.clear()

    async def after_action(self):
        self.robot.parked = True
        await self.planner._sio_ns.emit("robot_end", self.robot.robot_id)


class GameActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(WaitAction(planner, self))

        ParkingAction.nb_robots = 0
        if Camp().color == Camp.Colors.blue:
            self.append(ParkingAction(planner, self, models.Pose(x=1500 + 150, y=-1000 + 450, O=None)))
            self.append(ParkingAction(planner, self, models.Pose(x=1500 + 150 + 450, y=-1000 + 450, O=None)))
        else:
            self.append(ParkingAction(planner, self, models.Pose(x=1500 - 150, y=-1000 + 450, O=None)))
            self.append(ParkingAction(planner, self, models.Pose(x=1500 - 150 - 450, y=-1000 + 450, O=None)))

        self.planner._start_positions[1] = 1
        self.planner._start_positions[2] = 4

import asyncio
from functools import partial
from time import sleep
from typing import Awaitable, Callable, NewType

from cogip.models.models import SpeedEnum
from cogip.tools import planner
from .context import GameContext
from .pose import AdaptedPose, Pose
from .strategy import Strategy
from . import cake, robot


# Fake forward declaration
Actions = NewType("Actions", int)


class Action:
    """
    This class represents an action of the game.
    It contains a list of Pose to reach in order.
    A function can be executed before the action starts and after it ends.
    """
    def __init__(
            self,
            name: str,
            actions: Actions | None = None,
            direct_score: int = 0,
            potential_score: int = 0):
        self.name = name
        self.actions = actions
        self.direct_score = direct_score
        self.potential_score = potential_score
        self.robot: "robot.Robot" | None = None
        self.poses: list[Pose] = []
        self.before_action_func: Callable[["planner.planner.Planner"], Awaitable[None]] | None = None
        self.after_action_func: Callable[["planner.planner.Planner"], Awaitable[None]] | None = None

    @property
    def weight(self) -> float:
        """
        Weight of the action.
        It can be used to choose the next action to select.
        This is the generic implementation.
        """
        return self.direct_score + 0.5 * self.potential_score

    async def act_before_action(self, planner: "planner.planner.Planner"):
        """
        Function executed before the action starts.

        Parameters:
            planner: the planner object to send it information or orders
        """
        if self.before_action_func:
            await self.before_action_func(planner)

    async def act_after_action(self, planner: "planner.planner.Planner"):
        """
        Function executed after the action ends.

        Parameters:
            planner: the planner object to send it information or orders
        """
        if self.after_action_func:
            await self.after_action_func(planner)

    async def recycle(self, planner: "planner.planner.Planner"):
        """
        Function called if the action is blocked and put back in the actions list

        Parameters:
            planner: the planner object to send it information or orders
        """
        pass


class Actions(list[Action]):
    """
    List of actions.
    Just inherits from list for now.
    """
    def __init__(self):
        super().__init__()


class ApprovalAction(Action):
    """
    Example of the simple action with a pose that calls a function of the action itself
    to reset the list of poses.
    The robot will go from a point to another in loop.
    """
    def __init__(self):
        super().__init__("Approval action")
        self.game_context = GameContext()
        self.default_poses = [
            AdaptedPose(
                x=self.game_context.table.x_min + 300,
                y=(self.game_context.table.y_max + self.game_context.table.y_min) / 2,
                O=0,
                max_speed_linear=SpeedEnum.NORMAL, max_speed_angular=SpeedEnum.NORMAL
            ),
            AdaptedPose(
                x=self.game_context.table.x_max - 300,
                y=(self.game_context.table.y_max + self.game_context.table.y_min) / 2,
                O=180,
                max_speed_linear=SpeedEnum.NORMAL, max_speed_angular=SpeedEnum.NORMAL,
                after_pose_func=self.areset
            )
        ]
        self.reset()

    async def areset(self):
        self.reset()

    def reset(self):
        self.poses = [pose.copy() for pose in self.default_poses]

    @property
    def weight(self) -> float:
        return 1000000.0


class BackAndForthAction(Action):
    """
    Example action that generate its poses depending of the robot's pose
    at the beginning of the action.
    The robot will go from the current position to its opposite position in loop.
    """
    def __init__(self, actions: Actions):
        super().__init__("BackAnForth action", actions)
        self.game_context = GameContext()

        self.before_action_func = self.compute_poses

    async def compute_poses(self, planner: "planner.planner.Planner") -> None:
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

    async def append_pose(self, pose: Pose, planner: "planner.planner.Planner") -> None:
        self.poses.append(pose)

    @property
    def weight(self) -> float:
        return 1000000.0


class SpeedTestAction(Action):
    """
    Dummy action for pid calibration.
    Same dummy pose in loop.
    """
    def __init__(self):
        super().__init__("Pid calibration action")
        self.pose = Pose()
        self.pose.after_pose_func = lambda planner: self.poses.append(self.pose)
        self.poses = [self.pose]

    @property
    def weight(self) -> float:
        return 1000000.0


class ApprovalActions(Actions):
    def __init__(self):
        super().__init__()
        self.append(ApprovalAction())


class BackAndForthActions(Actions):
    def __init__(self):
        super().__init__()
        self.append(BackAndForthAction(self))
        self.append(BackAndForthAction(self))
        self.append(BackAndForthAction(self))
        self.append(BackAndForthAction(self))


class GameActions(Actions):
    def __init__(self):
        super().__init__()


class SpeedTestActions(Actions):
    def __init__(self):
        super().__init__()
        self.append(SpeedTestAction())


first_sleep = True


# Get cakes actions, one for each slot (12)
class GetCakesAtSlotAction(Action):
    def __init__(self, slot: "cake.CakeSlot"):
        global first_sleep
        super().__init__(f"Get cakes action at ({int(slot.x)}, {int(slot.y)})")
        self.slot = slot
        self.cake = slot.cake
        self.game_context = GameContext()
        self.init_action()
        first_sleep = True

    def init_action(self):
        self.pose = Pose(
            x=self.slot.x, y=self.slot.y, O=None, allow_reverse=False,
            max_speed_linear=SpeedEnum.NORMAL, max_speed_angular=SpeedEnum.NORMAL
        )
        self.pose.before_pose_func = self.before_pose
        self.pose.after_pose_func = self.after_pose
        self.poses = [self.pose]

    async def before_pose(self, planner: "planner.planner.Planner"):
        self.slot.cake.robot = self.robot
        planner.update_cake_obstacles(self.robot.robot_id)
        global first_sleep
        if first_sleep:
            first_sleep = False
            debug(f"Robot {self.robot.robot_id}; sleep first")
            await asyncio.sleep(10)
            debug(f"Robot {self.robot.robot_id}; wake up")

    async def after_pose(self, planner: "planner.planner.Planner"):
        self.slot.cake.on_table = False
        self.slot.cake = None

    async def recycle(self, planner: "planner.planner.Planner"):
        self.slot.cake = self.cake
        self.slot.cake.robot = None
        planner.update_cake_obstacles(self.robot.robot_id)
        self.init_action()


class TrainingActions(Actions):
    def __init__(self):
        super().__init__()
        self.game_context = GameContext()

        for slot in self.game_context.cake_slots:
            self.append(GetCakesAtSlotAction(slot))


action_classes = {
    Strategy.Approval: ApprovalActions,
    Strategy.Game: GameActions,
    Strategy.BackAndForth: BackAndForthActions,
    Strategy.AngularSpeedTest: SpeedTestActions,
    Strategy.LinearSpeedTest: SpeedTestActions,
    Strategy.Training: TrainingActions,
}

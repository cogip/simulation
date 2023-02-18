from functools import partial
from typing import Callable, NewType

import socketio

from cogip.models.models import SpeedEnum
from .pose import AdaptedPose, Pose
from .strategy import Strategy
from . import robot


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
        self.before_action_func: Callable[[socketio.ClientNamespace], None] = lambda sio: None
        self.after_action_func: Callable[[socketio.ClientNamespace], None] = lambda sio: None

    @property
    def weight(self) -> float:
        """
        Weight of the action.
        It can be used to choose the next action to select.
        This is the generic implementation.
        """
        return self.direct_score + 0.5 * self.potential_score

    def act_before_action(self, sio: socketio.ClientNamespace) -> None:
        """
        Function executed before the action starts.

        Parameters:
            sio: SocketIO client to emit message to the server
        """
        self.before_action_func(sio)

    def act_after_action(self, sio: socketio.ClientNamespace) -> None:
        """
        Function executed after the action ends.

        Parameters:
            sio: SocketIO client to emit message to the server
        """
        self.after_action_func(sio)


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
        self.reset()

    def reset(self, sio: socketio.ClientNamespace | None = None) -> None:
        self.poses = [
            AdaptedPose(x=300, y=-700, O=0, max_speed_linear=SpeedEnum.NORMAL, max_speed_angular=SpeedEnum.NORMAL),
            AdaptedPose(x=2700, y=-700, O=180, max_speed_linear=SpeedEnum.NORMAL, max_speed_angular=SpeedEnum.NORMAL)
        ]
        self.poses[-1].after_pose_func = self.reset

    @property
    def weight(self) -> float:
        return 1000000.0


class BackAndForthAction(Action):
    """
    Example action that generate its poses depending of the robot's pose
    at the begining of the action.
    The robot will go from the current position to its opposite position in loop.
    """
    def __init__(self, actions: Actions):
        super().__init__("BackAnForth action", actions)
        self.before_action_func = self.compute_poses

    def compute_poses(self, sio: socketio.ClientNamespace) -> None:
        x = 3000 - self.robot.pose_current.x
        y = -self.robot.pose_current.y
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

    def append_pose(self, pose: Pose, sio: socketio.ClientNamespace) -> None:
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
        self.pose.after_pose_func = lambda sio: self.poses.append(self.pose)
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


action_classes = {
    Strategy.Approval: ApprovalActions,
    Strategy.Game: GameActions,
    Strategy.BackAndForth: BackAndForthActions,
    Strategy.AngularSpeedTest: SpeedTestActions,
    Strategy.LinearSpeedTest: SpeedTestActions,
}

from functools import partial
from gpiozero import Button
from gpiozero.pins.mock import MockFactory
from gpiozero.pins.pigpio import PiGPIOFactory

from cogip.models import models
from cogip.tools import planner
from cogip.tools.copilot.controller import ControllerEnum
from . import actions, context, pose


class Robot:
    """
    Class representing a robot context.
    """
    def __init__(self, robot_id: int, planner: "planner.planner.Planner", virtual: bool):
        self.robot_id = robot_id
        self.planner = planner
        self.virtual = virtual
        self.game_context = context.GameContext()
        self.action: actions.Action | None = None
        self._pose_reached: bool = True
        self._pose_current: models.Pose | None = None
        self._pose_order: pose.Pose | None = None
        self.avoidance_path: list[pose.Pose] = []
        self.last_avoidance_pose_current: models.Pose | None = None
        self.last_emitted_pose_order: models.PathPose | None = None
        self._controller: ControllerEnum = self.game_context.default_controller
        controllers = self.planner._shared_properties["controllers"]
        controllers[robot_id] = self._controller
        self.planner._shared_properties["controllers"] = controllers
        self._obstacles: models.DynObstacleList = []
        self.starter: Button | None = None

        if virtual:
            starter = Button(
                17 if robot_id == 1 else 27,
                pull_up=True,
                bounce_time=0.1,
                pin_factory=MockFactory()
            )
        else:
            starter = Button(
                17,
                pull_up=None,
                bounce_time=None,
                active_state=False,
                pin_factory=PiGPIOFactory(host=f"robot{robot_id}")
            )

        starter.when_pressed = partial(planner.starter_changed, robot_id, True)
        starter.when_released = partial(planner.starter_changed, robot_id, False)
        self.starter = starter

    def set_pose_start(self, pose: pose.Pose):
        """
        Set the start pose.
        """
        self.action = None
        self.pose_current = pose.pose
        self.pose_order = pose
        self._pose_reached = True
        self.avoidance_path = []
        self.planner.set_pose_start(self.robot_id, self.pose_order)
        self.pose_order.act_after_pose(self.planner)

    @property
    def pose_reached(self) -> bool:
        return self._pose_reached

    @pose_reached.setter
    def pose_reached(self, reached: bool = True):
        """
        Set pose reached.
        If reached, a new pose and new action is selected.
        """
        if reached and not self.pose_reached and self.pose_order:
            self.pose_order.act_after_pose(self.planner)
        self._pose_reached = reached
        self.pose_order = None
        self.avoidance_path = []
        if self.action and len(self.action.poses) == 0:
            self.action.act_after_action(self.planner)
            self.action = None

    @property
    def pose_current(self) -> models.Pose:
        return self._pose_current

    @pose_current.setter
    def pose_current(self, new_pose: models.Pose):
        self._pose_current = new_pose
        self.planner._shared_poses_current[self.robot_id] = new_pose.dict(exclude_unset=True)

    @property
    def pose_order(self) -> pose.Pose | None:
        return self._pose_order

    @pose_order.setter
    def pose_order(self, new_pose: pose.Pose | None):
        self._pose_order = new_pose
        if new_pose is None and self.robot_id in self.planner._shared_poses_order:
            del self.planner._shared_poses_order[self.robot_id]
        elif new_pose is not None:
            self.planner._shared_poses_order[self.robot_id] = new_pose.path_pose.dict(exclude_unset=True)

    @property
    def controller(self) -> ControllerEnum:
        return self._controller

    @controller.setter
    def controller(self, new_controller: ControllerEnum):
        self._controller = new_controller
        controllers = self.planner._shared_properties["controllers"]
        controllers[self.robot_id] = new_controller
        self.planner._shared_properties["controllers"] = controllers

    @property
    def obstacles(self) -> models.DynObstacleList:
        return self._obstacles

    @obstacles.setter
    def obstacles(self, obstacles: models.DynObstacleList):
        self._obstacles = obstacles
        self.planner._shared_obstacles[self.robot_id] = [
            obstacle.dict(exclude_defaults=True)
            for obstacle in obstacles
        ]

    def next_pose(self) -> pose.Pose | None:
        """
        Select next pose.
        Returns None if no more pose is available in the current action.
        """
        self._pose_reached = False
        if not self.action or len(self.action.poses) == 0:
            self.action = None
            return None

        self.pose_order = self.action.poses.pop(0)
        self.pose_order.act_before_pose(self.planner)
        self.planner.set_pose_order(self.robot_id, self.pose_order)
        return self.pose_order

    def set_action(self, action: "actions.Action"):
        """
        Set current action.
        """
        self.action = action
        self.action.act_before_action(self.planner)
        self.next_pose()

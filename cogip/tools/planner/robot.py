import asyncio
from multiprocessing.managers import Namespace
from typing import TYPE_CHECKING

from functools import partial
from gpiozero import Button
from gpiozero.pins.mock import MockFactory
from gpiozero.pins.pigpio import PiGPIOFactory

from cogip.models import models
from cogip.tools.copilot.controller import ControllerEnum
from .actions import actions
from . import cake, context, logger, pose
from .strategy import Strategy

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


class Robot:
    """
    Class representing a robot context.
    """
    def __init__(self, robot_id: int, planner: "Planner", virtual: bool):
        self.namespace: Namespace = planner._process_manager.Namespace()
        self.robot_id = robot_id
        self.namespace.robot_id = robot_id
        self.planner = planner
        self.virtual = virtual
        self.game_context = context.GameContext()
        self.action: actions.Action | None = None
        self.pose_reached: bool = True
        self._pose_current: models.Pose | None = None
        self._pose_order: pose.Pose | None = None
        self.avoidance_path: list[pose.Pose] = []
        self.last_avoidance_pose_current: models.Pose | None = None
        self.last_emitted_pose_order: models.PathPose | None = None
        self.controller: ControllerEnum | None = None
        self._obstacles: models.DynObstacleList = []
        self.starter: Button | None = None
        self.blocked: int = 0
        self.cake: "cake.Cake" | None = None
        self.nb_cherries = 5
        self.parked = False
        self.sio_receiver_queue = asyncio.Queue()

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

        starter.when_pressed = partial(planner._sio_emitter_queues[robot_id].put, ("starter_changed", True))
        starter.when_released = partial(planner._sio_emitter_queues[robot_id].put, ("starter_changed", False))
        self.starter = starter

    async def set_pose_start(self, pose: models.Pose):
        """
        Set the start pose.
        """
        self.action = None
        self.pose_current = pose.copy()
        self.pose_order = None
        self.pose_reached = True
        self.avoidance_path = []
        await self.planner.set_pose_start(self.robot_id, self.pose_current)

    async def set_pose_reached(self, reached: bool = True):
        """
        Set pose reached.
        If reached, a new pose and new action is selected.
        """
        logger.debug(f"Robot {self.robot_id}: set_pose_reached({reached})")
        self.avoidance_path = []
        if reached and not self.pose_reached and (pose_order := self.pose_order):
            self.pose_order = None
            await pose_order.act_after_pose()
        else:
            self.pose_order = None
        self.pose_reached = reached
        if (action := self.action) and len(self.action.poses) == 0:
            self.action = None
            await action.act_after_action()

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
            if self.robot_id in self.planner._shared_last_avoidance_pose_currents:
                del self.planner._shared_last_avoidance_pose_currents[self.robot_id]

    async def set_controller(self, new_controller: ControllerEnum):
        if self.controller == new_controller:
            return
        self.controller = new_controller
        self.namespace.controller = new_controller.value
        await self.planner._sio_ns.emit("set_controller", (self.robot_id, self.controller.value))

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

    async def next_pose(self) -> pose.Pose | None:
        """
        Select next pose.
        Returns None if no more pose is available in the current action.
        """
        logger.debug(f"Robot {self.robot_id}: next_pose()")
        self.pose_reached = False
        if not self.action:
            return None

        if len(self.action.poses) == 0:
            return None

        pose_order = self.action.poses.pop(0)
        self.pose_order = None
        await pose_order.act_before_pose()
        self.blocked = 0
        self.pose_order = pose_order

        if self.game_context.strategy in [Strategy.LinearSpeedTest, Strategy.AngularSpeedTest]:
            await self.planner._sio_ns.emit("pose_order", (self.robot_id, self.pose_order.pose.dict()))

        return self.pose_order

    async def set_action(self, action: "actions.Action") -> pose.Pose | None:
        """
        Set current action.
        """
        logger.debug(f"Robot {self.robot_id}: set action '{action.name}'")
        self.pose_order = None
        self.action = action
        await self.action.act_before_action()
        return await self.next_pose()

import asyncio
from typing import TYPE_CHECKING

from .. import actuators
from ..avoidance.avoidance import AvoidanceStrategy
from ..camp import Camp
from ..pose import AdaptedPose, Pose
from .actions import Action, Actions

if TYPE_CHECKING:
    from ..planner import Planner


class AlignAction(Action):
    """
    Action used align the robot before game start.
    """

    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("Align action", planner, actions)
        self.before_action_func = self.init_poses

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.game_context.avoidance_strategy = new_strategy
        self.planner.shared_properties["avoidance_strategy"] = new_strategy

    async def init_poses(self):
        self.start_pose = self.planner.pose_current.model_copy()
        self.start_avoidance = self.game_context.avoidance_strategy

        await asyncio.gather(
            actuators.bottom_grip_close(self.planner),
            actuators.top_grip_close(self.planner),
            actuators.arm_panel_close(self.planner),
            actuators.cart_in(self.planner),
            asyncio.sleep(0.5),
        )
        await asyncio.gather(
            actuators.bottom_lift_up(self.planner),
            actuators.top_lift_up(self.planner),
        )

        if Camp().adapt_y(self.start_pose.y) > 0:
            # Do not do alignment if the robot is in the opposite start position because it is not in a corner
            return

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-1700 + self.game_context.properties.robot_length / 2,
            O=0,
            max_speed_linear=5,
            max_speed_angular=5,
            allow_reverse=True,
            bypass_anti_blocking=True,
            timeout_ms=0,  # TODO
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

    async def before_pose1(self):
        self.set_avoidance(AvoidanceStrategy.Disabled)

    async def after_pose1(self):
        self.set_avoidance(self.start_avoidance)
        current_pose = self.planner.pose_current.model_copy()
        current_pose.y = Camp().adapt_y(-1500 + self.game_context.properties.robot_length / 2)
        current_pose.O = Camp().adapt_angle(90)
        await self.planner.sio_ns.emit("pose_start", current_pose.model_dump())

        pose2 = AdaptedPose(
            x=current_pose.x,
            y=-1250,
            O=180 if current_pose.x > 0 else 0,
            max_speed_linear=20,
            max_speed_angular=20,
            allow_reverse=False,
        )
        self.poses.append(pose2)

        if current_pose.x > 0:
            x = 1200 - self.game_context.properties.robot_length / 2
        else:
            x = -1200 + self.game_context.properties.robot_length / 2
        pose3 = AdaptedPose(
            x=x,
            y=-1250,
            O=0,
            max_speed_linear=5,
            max_speed_angular=5,
            allow_reverse=True,
            bypass_anti_blocking=True,
            timeout_ms=0,  # TODO
            bypass_final_orientation=True,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

    async def before_pose3(self):
        self.set_avoidance(AvoidanceStrategy.Disabled)

    async def after_pose3(self):
        self.set_avoidance(self.start_avoidance)
        current_pose = self.planner.pose_current.model_copy()
        if current_pose.x > 0:
            current_pose.x = 1000 - self.game_context.properties.robot_length / 2
        else:
            current_pose.x = -1000 + self.game_context.properties.robot_length / 2
        current_pose.O = 180 if current_pose.x > 0 else 0
        await self.planner.sio_ns.emit("pose_start", current_pose.model_dump())

        pose4 = Pose(
            x=730 if current_pose.x > 0 else -730,
            y=current_pose.y,
            O=current_pose.O,
            max_speed_linear=33,
            max_speed_angular=33,
            allow_reverse=False,
        )
        self.poses.append(pose4)

        pose5 = Pose(
            x=self.start_pose.x,
            y=self.start_pose.y,
            O=self.start_pose.O,
            max_speed_linear=33,
            max_speed_angular=33,
            allow_reverse=True,
        )
        self.poses.append(pose5)

    def weight(self) -> float:
        return 1000000.0

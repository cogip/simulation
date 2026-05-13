import asyncio
from typing import TYPE_CHECKING

from colorzero import Color

from cogip.cpp.libraries.models import MotionDirection
from cogip.models.artifacts import FixedObstacleID
from cogip.tools.planner import actuators
from cogip.tools.planner.actions.action import Action
from cogip.tools.planner.actions.strategy import Strategy
from cogip.tools.planner.actions.utils import get_relative_pose, set_countdown_color
from cogip.tools.planner.avoidance.avoidance import AvoidanceStrategy
from cogip.tools.planner.pose import AdaptedPose, Pose
from cogip.tools.planner.table import TableEnum

if TYPE_CHECKING:
    from ..planner import Planner


# Delay after each obstacle toggle so avoidance and monitor see the new state.
OBSTACLE_TOGGLE_DELAY_S = 0.2


class NinjaAction(Action):
    """
    Ninja action.
    """

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = True):
        super().__init__("Ninja action", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        self.start_pose = self.pose_current.model_copy()

        pose1 = AdaptedPose(
            x=self.start_pose.x,
            y=-700,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            x=825,
            y=-700,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        pose3 = AdaptedPose(
            x=860,
            y=-700,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        if self.planner.shared_properties.table == TableEnum.Training:
            pose1.x -= 1000
            pose2.x -= 1000
            pose3.x -= 1000

    async def before_pose1(self):
        self.logger.info(f"{self.name}: before_pose1")
        self.planner.led.color = Color("green")
        await set_countdown_color(self.planner, "green")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        await actuators.ninja_arms_side(self.planner, speed=500)

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        await actuators.ninja_arms_close(self.planner, speed=0)

    async def before_pose3(self):
        self.logger.info(f"{self.name}: before_pose3")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")

    def weight(self) -> float:
        return 9_999_999.0


class NinjaExposeFourAction(Action):
    """No-arm clone of NinjaDropFourAction for validating the path alone."""

    DROP_FOUR_2_RECUL_MM = 265  # pose 2: back to raw x=625 from pose 1 at x=880
    DROP_FOUR_6_NORTH_MM = 265  # pose 6: forward to raw x=880 from pose 2 at x=625

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja expose four", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        # Chain built in raw (blue camp) coords; each pose wraps it in AdaptedPose for leaf-level camp adaptation.

        # pose 1: 205 mm north of NinjaDropZone (raw x=880), facing north, BIDIRECTIONAL.
        drop_zone_obstacle = self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone]
        drop_zone_anchor = Pose(x=drop_zone_obstacle.x, y=drop_zone_obstacle.y, O=0)
        chain = get_relative_pose(drop_zone_anchor, front_offset=205, side_offset=0, angular_offset=0)
        pose1 = AdaptedPose(
            **chain.model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        # 2: south recul to raw x=625, along pose 1's heading (raw +x axis).
        chain = get_relative_pose(chain, front_offset=-self.DROP_FOUR_2_RECUL_MM)
        pose2 = AdaptedPose(
            **chain.model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        # 6: north return to raw x=880, forming the N-S-N corridor with poses 1 and 2.
        chain = get_relative_pose(chain, front_offset=self.DROP_FOUR_6_NORTH_MM)
        pose6 = AdaptedPose(
            **chain.model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose6,
            after_pose_func=self.after_pose6,
        )
        self.poses.append(pose6)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        # Drop the start-area DropZone so the next poses can drive through it.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone].enabled = False
        self.logger.info(f"{self.name}: after_pose1 - NinjaDropZone disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")

    async def before_pose6(self):
        self.logger.info(f"{self.name}: before_pose6")

    async def after_pose6(self):
        self.logger.info(f"{self.name}: after_pose6")

    def weight(self) -> float:
        # Runs first; comment one of ExposeFour/DropFour out in NinjaStrategy to pick one.
        return 11_000_000.0


class NinjaDropFourAction(Action):
    """Drop four items via a shake pattern (approach, deposit, shake, close)."""

    DROP_FOUR_2_RECUL_MM = 50  # pose 2: back 250 mm from pose 1
    DROP_FOUR_2b_RECUL_MM = 140  # pose 2: back 250 mm from pose 1
    DROP_FOUR_3_FORWARD_MM = 150  # pose 3: forward 190 mm from pose 2 (current)
    DROP_FOUR_6_NORTH_MM = 40  # pose 6: 40 mm north (raw +x) from pose 5
    DROP_FOUR_8_EAST_MM = 100  # pose 8: 120 mm east (display) from pose 7 (current)
    DROP_FOUR_9_WEST_MM = 40  # pose 9: 40 mm west (display) from pose 8 (current)
    DROP_FOUR_10_X_TARGET = 880  # pose 10: north to absolute raw x = 880

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja drop four", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait
        # Poses 8, 9, 10 computed at runtime from the robot's current pose.
        self._pose8: Pose | None = None
        self._pose9: Pose | None = None
        self._pose10: Pose | None = None

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        # Chain built in raw (blue camp) coords; each pose wraps it in AdaptedPose for leaf-level camp adaptation.

        # pose 1: 205 mm north of NinjaDropZone (raw x=880), facing north, BIDIRECTIONAL.
        drop_zone_obstacle = self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone]
        drop_zone_anchor = Pose(x=drop_zone_obstacle.x, y=drop_zone_obstacle.y, O=0)
        chain = get_relative_pose(drop_zone_anchor, front_offset=205, side_offset=0, angular_offset=0)
        pose1 = AdaptedPose(
            **chain.model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        # 2: recul along pose 1's heading; arms_side deploys in parallel with the slow BWD drive.
        chain = get_relative_pose(chain, front_offset=-self.DROP_FOUR_2_RECUL_MM)
        pose2 = AdaptedPose(
            **chain.model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose2,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        # 2b: continued recul, faster final approach speed.
        chain = get_relative_pose(chain, front_offset=-self.DROP_FOUR_2b_RECUL_MM)
        pose2b = AdaptedPose(
            **chain.model_dump(),
            max_speed_linear=30,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose2b,
            after_pose_func=self.after_pose2b,
        )
        self.poses.append(pose2b)

        # 3: forward relative to pose 2b (along pose 2b's heading).
        chain = get_relative_pose(chain, front_offset=self.DROP_FOUR_3_FORWARD_MM)
        pose3 = AdaptedPose(
            **chain.model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        # 6: north of pose 3; arms_close fires in before_pose6 in parallel with the move.
        chain = get_relative_pose(chain, front_offset=self.DROP_FOUR_6_NORTH_MM)
        pose6 = AdaptedPose(
            **chain.model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose6,
            after_pose_func=self.after_pose6,
        )
        self.poses.append(pose6)

        # 6b: clearance pose north of pose 7 (raw x=880, y=-545, facing north) to smooth the transit to pose 7.
        pose6b = AdaptedPose(
            x=880,
            y=-545,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose6b,
        )
        self.poses.append(pose6b)

        # 7: 10 mm west of NinjaDropZone facing east; before_pose7 re-enables the zone for avoidance.
        chain = get_relative_pose(chain, front_offset=-215, side_offset=165, angular_offset=-90)
        pose7 = AdaptedPose(
            **chain.model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose7,
            after_pose_func=self.after_pose7,
        )
        self.poses.append(pose7)

        # 8: 120 mm east of pose 7, reached BACKWARD (end facing west). Target computed at runtime.
        self._pose8 = Pose(
            x=0,
            y=0,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose8,
            after_pose_func=self.after_pose8,
        )
        self.poses.append(self._pose8)

        # 9: 40 mm west of pose 8, reached FORWARD (ends facing west). Target computed at runtime.
        self._pose9 = Pose(
            x=0,
            y=0,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose9,
            after_pose_func=self.after_pose9,
        )
        self.poses.append(self._pose9)

        # 10: drive north to raw x=880 out of the DropZone, keeping y, facing north. Runtime target.
        self._pose10 = Pose(
            x=0,
            y=0,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose10,
            after_pose_func=self.after_pose10,
        )
        self.poses.append(self._pose10)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)
        # First deposit done: drop the start-area DropZone so the next poses can drive through it.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone].enabled = False
        self.logger.info(f"{self.name}: after_pose1 - NinjaDropZone disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def before_pose2(self):
        self.logger.info(f"{self.name}: before_pose2 - deploying arms_side")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")
        await actuators.ninja_arms_side(self.planner, speed=1000)
        await asyncio.sleep(1)

    async def before_pose2b(self):
        self.logger.info(f"{self.name}: before_pose2")

    async def after_pose2b(self):
        self.logger.info(f"{self.name}: after_pose2")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def before_pose6(self):
        self.logger.info(f"{self.name}: before_pose6 - closing arms")

    async def after_pose6(self):
        self.logger.info(f"{self.name}: after_pose6")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose6b(self):
        self.logger.info(f"{self.name}: after_pose6b")

    async def before_pose7(self):
        self.logger.info(f"{self.name}: before_pose7 - re-enabling NinjaDropZone")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone].enabled = True
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose7(self):
        self.logger.info(f"{self.name}: after_pose7")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def before_pose8(self):
        cur = self.planner.pose_current
        # 120 mm east (display), ending facing west; AdaptedPose keeps the delta camp-correct.
        delta = AdaptedPose(x=0, y=-self.DROP_FOUR_8_EAST_MM, O=90)
        self._pose8.x = cur.x + delta.x
        self._pose8.y = cur.y + delta.y
        self._pose8.O = delta.O
        self.logger.info(
            f"{self.name}: before_pose8 target ({self._pose8.x:.1f}, "
            f"{self._pose8.y:.1f}, {self._pose8.O:.1f}) from "
            f"current ({cur.x:.1f}, {cur.y:.1f}, {cur.O:.1f})"
        )

    async def after_pose8(self):
        self.logger.info(f"{self.name}: after_pose8")

    async def before_pose9(self):
        cur = self.planner.pose_current
        # 40 mm west (display), FORWARD ending facing west; AdaptedPose keeps the delta camp-correct.
        delta = AdaptedPose(x=0, y=self.DROP_FOUR_9_WEST_MM, O=90)
        self._pose9.x = cur.x + delta.x
        self._pose9.y = cur.y + delta.y
        self._pose9.O = delta.O
        self.logger.info(
            f"{self.name}: before_pose9 target ({self._pose9.x:.1f}, "
            f"{self._pose9.y:.1f}, {self._pose9.O:.1f}) from "
            f"current ({cur.x:.1f}, {cur.y:.1f}, {cur.O:.1f})"
        )

    async def after_pose9(self):
        self.logger.info(f"{self.name}: after_pose9")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDropZone].enabled = False
        self.logger.info(f"{self.name}: after_pose9 - NinjaDropZone disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone].enabled = True
        self.logger.info(f"{self.name}: after_pose9 - NinjaCratesZone enabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def before_pose10(self):
        cur = self.planner.pose_current
        # Drive north to raw x=DROP_FOUR_10_X_TARGET, keeping y, facing north.
        self._pose10.x = self.DROP_FOUR_10_X_TARGET
        self._pose10.y = cur.y
        self._pose10.O = 0
        self.logger.info(
            f"{self.name}: before_pose10 target ({self._pose10.x:.1f}, "
            f"{self._pose10.y:.1f}, {self._pose10.O:.1f}) from "
            f"current ({cur.x:.1f}, {cur.y:.1f}, {cur.O:.1f})"
        )

    async def after_pose10(self):
        self.logger.info(f"{self.name}: after_pose10")

    def weight(self) -> float:
        # Highest weight: runs first in the standalone strategy.
        return 11_000_000.0


class NinjaBuildGroupAction(Action):
    """Build the Ninja group of 4: collect the four items and stack them for the pantry."""

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja build group", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        # Disable NinjaArea1: poses 1 to 5b operate inside its inflated bbox.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaArea1].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

        # Anchors at the two nut crate zone centers (raw blue); AdaptedPose camp-adapts each pose.
        area1_anchor = Pose(x=725, y=-400, O=0)
        area2_anchor = Pose(x=775, y=-150, O=0)

        # === Area 1 (poses 1..5b) ===

        pose1 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=165, side_offset=0, angular_offset=180).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        pose2 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=115, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        pose3 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=165, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        pose4 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=25, side_offset=0, angular_offset=180).model_dump(),
            max_speed_linear=10,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4,
        )
        self.poses.append(pose4)

        pose5b = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=75, side_offset=0, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose5b,
        )
        self.poses.append(pose5b)

        # === Transition + Area 2 (poses 6..16) ===

        pose6 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=-125, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose6,
            after_pose_func=self.after_pose6,
        )
        self.poses.append(pose6)

        pose7 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=-50, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose7,
        )
        self.poses.append(pose7)

        pose8 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=-75, angular_offset=-90).model_dump(),
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose8,
        )
        self.poses.append(pose8)

        pose9 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=0, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose9,
        )
        self.poses.append(pose9)

        pose10 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=-50, angular_offset=90).model_dump(),
            max_speed_linear=33,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose10,
        )
        self.poses.append(pose10)

        pose11 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=0, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose11,
        )
        self.poses.append(pose11)

        pose12 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=-50, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose12,
        )
        self.poses.append(pose12)

        pose13 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=0, side_offset=50, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose13,
        )
        self.poses.append(pose13)

        pose14 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=50, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose14,
        )
        self.poses.append(pose14)

        pose15 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=-10, angular_offset=90).model_dump(),
            max_speed_linear=20,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose15,
        )
        self.poses.append(pose15)

        pose16 = AdaptedPose(
            **get_relative_pose(area2_anchor, front_offset=-125, side_offset=90, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose16,
        )
        self.poses.append(pose16)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2")

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3")

    async def after_pose4(self):
        self.logger.info(f"{self.name}: after_pose4")

    async def after_pose5b(self):
        self.logger.info(f"{self.name}: after_pose5b")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def before_pose6(self):
        self.logger.info(f"{self.name}: before_pose6 - disabling NinjaArea2")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaArea2].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose6(self):
        self.logger.info(f"{self.name}: after_pose6")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose7(self):
        self.logger.info(f"{self.name}: after_pose7")

    async def after_pose8(self):
        self.logger.info(f"{self.name}: after_pose8")

    async def after_pose9(self):
        self.logger.info(f"{self.name}: after_pose9")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose10(self):
        self.logger.info(f"{self.name}: after_pose10")

    async def after_pose11(self):
        self.logger.info(f"{self.name}: after_pose11")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose12(self):
        self.logger.info(f"{self.name}: after_pose12")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose13(self):
        self.logger.info(f"{self.name}: after_pose13")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose14(self):
        self.logger.info(f"{self.name}: after_pose14")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose15(self):
        self.logger.info(f"{self.name}: after_pose15")

    async def after_pose16(self):
        self.logger.info(f"{self.name}: after_pose16")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    def weight(self) -> float:
        # Higher than NinjaPantryDepositAction so the build group runs first.
        return 10_000_000.0


class NinjaPantryDepositAction(Action):
    """Deposit the assembled group at the pantry in two passes, then clear out."""

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja pantry deposit", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    async def before_action(self):
        # NinjaArea1/2 already disabled by NinjaBuildGroupAction. Enable NinjaDeposit so the
        # released crates show and avoidance routes around them.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = True
        self.logger.info(f"{self.name}: NinjaDeposit enabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

        area1_anchor = Pose(x=725, y=-400, O=0)
        deposit_obstacle = self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit]
        deposit_anchor = Pose(x=deposit_obstacle.x, y=deposit_obstacle.y, O=0)

        # 17: 205 mm north of the deposit zone center (raw x=880), facing north; capped to stay on the table.
        pose17 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=205, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose17,
        )
        self.poses.append(pose17)

        # 18: descend to x=750 backward (N-S corridor 17/18/19); NinjaDeposit disabled in before_pose18.
        pose18 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=25, side_offset=150, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose18,
            after_pose_func=self.after_pose18,
        )
        self.poses.append(pose18)

        # 19: climb back north to x=880, still facing north (forward).
        pose19 = AdaptedPose(
            **get_relative_pose(area1_anchor, front_offset=155, side_offset=150, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose19,
        )
        self.poses.append(pose19)

        # 20: park east of NinjaDeposit facing west; before_pose20 re-enables the zone for avoidance.
        pose20 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=-40, side_offset=-340, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose20,
            after_pose_func=self.after_pose20,
        )
        self.poses.append(pose20)

        # 21: drive west backward to 10 mm east of the zone's east edge.
        pose21 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=-40, side_offset=-180, angular_offset=-90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose21,
        )
        self.poses.append(pose21)

        # 22: back up 50 mm east of pose 21.
        pose22 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=-40, side_offset=-230, angular_offset=90).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose22,
        )
        self.poses.append(pose22)

        # 23/24/25: replay the N-S-N corridor with a deeper south dip for the second pass.
        pose23 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=205, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose23,
        )
        self.poses.append(pose23)

        pose24 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=-60, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose24,
            after_pose_func=self.after_pose24,
        )
        self.poses.append(pose24)

        pose25 = AdaptedPose(
            **get_relative_pose(deposit_anchor, front_offset=205, side_offset=0, angular_offset=0).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose25,
        )
        self.poses.append(pose25)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose17(self):
        self.logger.info(f"{self.name}: after_pose17")

    async def before_pose18(self):
        self.logger.info(f"{self.name}: before_pose18 - disabling NinjaDeposit")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose18(self):
        self.logger.info(f"{self.name}: after_pose18")

    async def after_pose19(self):
        self.logger.info(f"{self.name}: after_pose19")

    async def before_pose20(self):
        self.logger.info(f"{self.name}: before_pose20 - enabling NinjaDeposit")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = True
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose20(self):
        self.logger.info(f"{self.name}: after_pose20")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose21(self):
        self.logger.info(f"{self.name}: after_pose21")

    async def after_pose22(self):
        self.logger.info(f"{self.name}: after_pose22")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = True
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose23(self):
        self.logger.info(f"{self.name}: after_pose23")

    async def before_pose24(self):
        self.logger.info(f"{self.name}: before_pose24 - disabling NinjaDeposit")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose24(self):
        self.logger.info(f"{self.name}: after_pose24")

    async def after_pose25(self):
        self.logger.info(f"{self.name}: after_pose25")
        # PantryDeposit done: drop NinjaDeposit so the next actions move freely.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaDeposit].enabled = False
        self.logger.info(f"{self.name}: after_pose25 - NinjaDeposit disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    def weight(self) -> float:
        # Dependency guard: wait until NinjaBuildGroupAction has run (removed from the strategy when picked).
        if any(isinstance(a, NinjaBuildGroupAction) for a in self.strategy):
            return 0
        return 9_999_999.0


class NinjaRottenDepositAction(Action):
    """Pick up two crates from NinjaCratesZone one at a time and deposit them at the rotten zone."""

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja rotten deposit", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    async def before_action(self):
        # Disable NinjaCratesZone so the pickup poses inside its inflated bbox are accepted.
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone].enabled = False
        self.logger.info(f"{self.name}: NinjaCratesZone disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

        # Approach: 40 mm west of pickup 1; the robot opens its arms here before the pickup.
        pose_approach = AdaptedPose(
            x=675,
            y=-550,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose_approach,
        )
        self.poses.append(pose_approach)

        # 1: pickup 1 at (675, -635, +90°) facing west, reached BACKWARD; arms_hold_one_long grabs the crate.
        pose1 = AdaptedPose(
            x=675,
            y=-635,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        # Clearance: 100 mm west of pickup 1 so the robot exits the zone straight, FORWARD.
        pose1_clear = AdaptedPose(
            x=675,
            y=-535,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose1_clear,
        )
        self.poses.append(pose1_clear)

        # 2: deposit 1 at (775, -280, -90°). arms_open at arrival.
        pose2 = AdaptedPose(
            x=775,
            y=-200,
            O=-90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose2)

        # Approach 2: 85 mm west of pickup 2; the robot re-opens its arms before the BACKWARD pickup.
        pose_approach2 = AdaptedPose(
            x=675,
            y=-600,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose_approach2,
        )
        self.poses.append(pose_approach2)

        # 3: pickup 2 at (675, -685, +90°), 50 mm east of pickup 1, reached BACKWARD; before_pose3 shrinks the zone.
        pose3 = AdaptedPose(
            x=675,
            y=-685,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BACKWARD_ONLY,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        # 4: deposit 2 at (725, -250, 90°). arms_open at arrival.
        pose4 = AdaptedPose(
            x=725,
            y=-250,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose4,
        )
        self.poses.append(pose4)

        # 5: deposit 2 at (725, -200, 90°). arms_close at arrival.
        pose5 = AdaptedPose(
            x=725,
            y=-200,
            O=90,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.FORWARD_ONLY,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose5,
        )
        self.poses.append(pose5)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def after_pose_approach(self):
        self.logger.info(f"{self.name}: after_pose_approach - opening arms")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone].enabled = False
        self.logger.info(f"{self.name}: after_pose9 - NinjaCratesZone disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1 - pickup 1")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose1_clear(self):
        self.logger.info(f"{self.name}: after_pose1_clear")

    async def after_pose2(self):
        self.logger.info(f"{self.name}: after_pose2 - deposit 1")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose_approach2(self):
        self.logger.info(f"{self.name}: after_pose_approach2 - opening arms")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def before_pose3(self):
        # First crate removed: shrink the zone 50 mm along y and shift center 25 mm east.
        zone = self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone]
        zone.length -= 50
        zone.y -= 25
        self.logger.info(f"{self.name}: before_pose3 - NinjaCratesZone shrunk (length={zone.length}, y={zone.y})")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3 - pickup 2")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose4(self):
        self.logger.info(f"{self.name}: after_pose4 - deposit 2")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose5(self):
        self.logger.info(f"{self.name}: after_pose5 - close")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    def weight(self) -> float:
        return 9_500_000.0


class NinjaAtTableAction(Action):
    """Final celebration: drive to the dinner spot and oscillate the arms forever."""

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja a table", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    async def before_action(self):
        pose3 = AdaptedPose(
            x=620,
            y=-200,
            O=45,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            before_pose_func=self.before_pose3,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose3)

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def before_pose3(self):
        self.logger.info(f"{self.name}: before_pose3 - disabling all fixed obstacles")
        for obstacle in self.planner.game_context.fixed_obstacles.values():
            obstacle.enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose3(self):
        self.logger.info(f"{self.name}: after_pose3 - spawning arm oscillation task")
        self.planner.final_action_task = asyncio.create_task(self._oscillate_arms())

    async def _oscillate_arms(self):
        try:
            while True:
                await actuators.ninja_arms_open(self.planner, speed=0)
                await asyncio.sleep(0.5)
                await actuators.ninja_arms_close(self.planner, speed=0)
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            self.logger.info(f"{self.name}: arm oscillation cancelled by reset")
            raise

    def weight(self) -> float:
        if self.planner.game_context.countdown > 5:
            return 0
        return 99_999_999.0


class NinjaHomologationAction(Action):
    """Homologation run: disable every Ninja obstacle and trace a fixed 4-pose path in FORWARD."""

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja homologation", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        # Disable every Ninja obstacle for a clean homologation course.
        for obstacle_id in (
            FixedObstacleID.NinjaArea1,
            FixedObstacleID.NinjaArea2,
            FixedObstacleID.NinjaDeposit,
            FixedObstacleID.NinjaDropZone,
            FixedObstacleID.NinjaCratesZone,
        ):
            self.planner.game_context.fixed_obstacles[obstacle_id].enabled = False
        self.logger.info(f"{self.name}: all Ninja obstacles disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

        waypoints = [
            (880, -600, 0),
            (750, -600, 0),
            (750, -100, 0),
            (880, -750, 90),
        ]
        for x, y, o in waypoints:
            self.poses.append(
                AdaptedPose(
                    x=x,
                    y=y,
                    O=o,
                    max_speed_linear=20,
                    max_speed_angular=100,
                    motion_direction=MotionDirection.FORWARD_ONLY,
                    bypass_final_orientation=True,
                )
            )

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    def weight(self) -> float:
        return 9_999_999.0


class NinjaOneByOneAction(Action):
    """Debug action: 4-iteration pickup/drop cycle west of NinjaCratesZone, each shifted 50 mm east."""

    def __init__(self, planner: "Planner", strategy: Strategy, *, wait: bool = False):
        super().__init__("Ninja one by one", planner, strategy, interruptable=True)
        self.before_action_func = self.before_action
        self.wait = wait
        self._pose_exit: Pose | None = None

    def set_avoidance(self, new_strategy: AvoidanceStrategy):
        self.logger.info(f"{self.name}: set avoidance to {new_strategy.name}")
        self.planner.shared_properties.avoidance_strategy = new_strategy.val

    async def before_action(self):
        self.set_avoidance(AvoidanceStrategy.AvoidanceCpp)

        # Disable every Ninja fixed obstacle except NinjaCratesZone.
        for obstacle_id in (
            FixedObstacleID.NinjaArea1,
            FixedObstacleID.NinjaArea2,
            FixedObstacleID.NinjaDeposit,
            FixedObstacleID.NinjaDropZone,
        ):
            self.planner.game_context.fixed_obstacles[obstacle_id].enabled = False
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone].enabled = True
        self.logger.info(f"{self.name}: NinjaCratesZone enabled, other Ninja obstacles disabled")
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

        # Exit pose: 100 mm west of the start, target computed at runtime from pose_current.
        self._pose_exit = Pose(
            x=0,
            y=0,
            O=0,
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose_exit,
            after_pose_func=self.after_pose_exit,
        )
        self.poses.append(self._pose_exit)

        # Park 200 mm west of the zone edge facing west; after_pose1 disables the zone for the cycle.
        crates_zone_obstacle = self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone]
        crates_anchor = Pose(x=crates_zone_obstacle.x, y=crates_zone_obstacle.y, O=0)
        zone_half_y = crates_zone_obstacle.length / 2
        pose1 = AdaptedPose(
            **get_relative_pose(
                crates_anchor,
                front_offset=0,
                side_offset=zone_half_y + 200,
                angular_offset=90,
            ).model_dump(),
            max_speed_linear=100,
            max_speed_angular=100,
            motion_direction=MotionDirection.BIDIRECTIONAL,
            bypass_final_orientation=False,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose1)

        # Pickup/drop cycle: 5 poses per iteration, repeated 4 times, each shifted +50 mm east.
        # Tuple: (distance_west_mm, angular_offset, motion_direction, bypass_final_orientation, max_speed, after_hook).
        subsequence = [
            # Approach: 150 mm west, arms_open; bypass=False locks the +90 heading for the next BWD reach.
            (110 + 150, 90, MotionDirection.FORWARD_ONLY, False, 100, self.after_pose_open),
            (110, 90, MotionDirection.BACKWARD_ONLY, True, 100, self.after_pose_hold),
            # Slow FWD west to 200 mm west of zone edge.
            (200, 90, MotionDirection.FORWARD_ONLY, True, 5, None),
            (400, -90, MotionDirection.BACKWARD_ONLY, True, 100, self.after_pose_open),
            (200, -90, MotionDirection.FORWARD_ONLY, True, 100, self.after_pose_close),
        ]
        # east_shift_mm subtracts from side_offset to move east (-y, raw blue); AdaptedPose mirrors for yellow.
        for east_shift_mm in (0, 50, 100, 150):
            for distance_west, heading, motion_dir, bypass_ori, max_speed, after_hook in subsequence:
                self.poses.append(
                    AdaptedPose(
                        **get_relative_pose(
                            crates_anchor,
                            front_offset=0,
                            side_offset=zone_half_y + distance_west - east_shift_mm,
                            angular_offset=heading,
                        ).model_dump(),
                        max_speed_linear=max_speed,
                        max_speed_angular=100,
                        motion_direction=motion_dir,
                        bypass_final_orientation=bypass_ori,
                        after_pose_func=after_hook,
                    )
                )

        if self.planner.shared_properties.table == TableEnum.Training:
            for pose in self.poses:
                pose.x -= 1000

    async def before_pose_exit(self):
        cur = self.planner.pose_current
        delta = AdaptedPose(x=0, y=100, O=0)
        self._pose_exit.x = cur.x + delta.x
        self._pose_exit.y = cur.y + delta.y
        self._pose_exit.O = cur.O
        self.logger.info(
            f"{self.name}: before_pose_exit target "
            f"({self._pose_exit.x:.1f}, {self._pose_exit.y:.1f}, {self._pose_exit.O:.1f}) "
            f"from current ({cur.x:.1f}, {cur.y:.1f}, {cur.O:.1f})"
        )

    async def after_pose_exit(self):
        self.logger.info(f"{self.name}: after_pose_exit")

    async def after_pose1(self):
        self.logger.info(f"{self.name}: after_pose1 - disabling NinjaCratesZone")
        self.planner.game_context.fixed_obstacles[FixedObstacleID.NinjaCratesZone].enabled = False
        await asyncio.sleep(OBSTACLE_TOGGLE_DELAY_S)

    async def after_pose_hold(self):
        self.logger.info(f"{self.name}: after_pose_hold - hold one long")
        await actuators.ninja_arms_hold_one_long(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose_open(self):
        self.logger.info(f"{self.name}: after_pose_open - arms open")
        await actuators.ninja_arms_open(self.planner, speed=0)
        await asyncio.sleep(0.5)

    async def after_pose_close(self):
        self.logger.info(f"{self.name}: after_pose_close - arms close")
        await actuators.ninja_arms_close(self.planner, speed=0)
        await asyncio.sleep(0.5)

    def weight(self) -> float:
        return 9_999_999.0


class NinjaStrategy(Strategy):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        # can_wait keeps a WaitAction running so the T-5s blocked() preemption has something to interrupt.
        self.can_wait = True
        # self.append(NinjaExposeFourAction(planner, self))
        # self.append(NinjaDropFourAction(planner, self))

        self.append(NinjaBuildGroupAction(planner, self))
        self.append(NinjaPantryDepositAction(planner, self))
        # self.append(NinjaRottenDepositAction(planner, self))
        self.append(NinjaAtTableAction(planner, self))
        # self.append(NinjaOneByOneAction(planner, self))
        # self.append(NinjaHomologationAction(planner, self))

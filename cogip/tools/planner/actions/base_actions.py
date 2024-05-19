import asyncio
import math
from typing import TYPE_CHECKING

from cogip.models import artifacts
from cogip.models.actuators import BoolSensorEnum
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


class GripAction(Action):
    """
    Action used to grip plants.
    """

    def __init__(self, planner: "Planner", actions: Actions, plant_supply_id: artifacts.PlantSupplyID):
        super().__init__("Grip action", planner, actions)
        self.before_action_func = self.before_action
        self.plant_supply = self.game_context.plant_supplies[plant_supply_id]
        self.stop_before_center_1 = 180

    async def recycle(self):
        self.plant_supply.enabled = True
        self.recycled = True

    async def before_action(self):
        # Compute first pose to get plants using bottom grips
        self.plant_supply.enabled = False
        self.start_pose = self.planner.pose_current.model_copy()
        dist_x = self.plant_supply.x - self.planner.pose_current.x
        dist_y = self.plant_supply.y - self.planner.pose_current.y
        dist = math.hypot(dist_x, dist_y)
        pose = Pose(
            x=self.plant_supply.x - dist_x / dist * self.stop_before_center_1,
            y=self.plant_supply.y - dist_y / dist * self.stop_before_center_1,
            O=0,
            max_speed_linear=30,
            max_speed_angular=30,
            allow_reverse=False,
            bypass_final_orientation=True,
            before_pose_func=self.before_pose1,
            intermediate_pose_func=self.intermediate_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose)

    async def before_pose1(self):
        await actuators.arm_panel_close(self.planner)
        await actuators.bottom_lift_down(self.planner)
        await asyncio.sleep(0.5)
        await actuators.top_lift_down(self.planner)
        await asyncio.sleep(0.5)
        await asyncio.gather(
            actuators.bottom_grip_open(self.planner),
            actuators.top_grip_open(self.planner),
        )

    async def intermediate_pose1(self):
        # Update first pose to take avoidance into account
        dist_x = self.plant_supply.x - self.planner.pose_current.x
        dist_y = self.plant_supply.y - self.planner.pose_current.y
        dist = math.hypot(dist_x, dist_y)
        self.planner.pose_order.x = self.plant_supply.x - dist_x / dist * self.stop_before_center_1
        self.planner.pose_order.y = self.plant_supply.y - dist_y / dist * self.stop_before_center_1
        self.planner.shared_properties["pose_order"] = self.planner.pose_order.path_pose.model_dump(exclude_unset=True)

    async def after_pose1(self):
        await actuators.top_grip_mid_open(self.planner)
        await asyncio.sleep(0.1)
        await actuators.top_grip_mid(self.planner)
        await asyncio.sleep(0.1)
        await actuators.top_grip_mid_close(self.planner)
        await asyncio.sleep(0.1)
        await actuators.top_grip_close(self.planner)
        await asyncio.sleep(0.1)

        if BoolSensorEnum.TOP_GRIP_LEFT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_LEFT].state = True
        if BoolSensorEnum.TOP_GRIP_RIGHT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_RIGHT].state = True

        # Step back
        back_dist = 100
        diff_x = back_dist * math.cos(math.radians(self.planner.pose_current.O))
        diff_y = back_dist * math.sin(math.radians(self.planner.pose_current.O))

        pose = Pose(
            x=self.planner.pose_current.x - diff_x,
            y=self.planner.pose_current.y - diff_y,
            O=0,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=True,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose)

    async def after_pose2(self):
        await actuators.top_lift_up(self.planner)
        await asyncio.sleep(0.5)

        # Compute pose to get plants using bottom grips
        forward_dist = 220
        diff_x = forward_dist * math.cos(math.radians(self.planner.pose_current.O))
        diff_y = forward_dist * math.sin(math.radians(self.planner.pose_current.O))

        pose = Pose(
            x=self.planner.pose_current.x + diff_x,
            y=self.planner.pose_current.y + diff_y,
            O=0,
            max_speed_linear=20,
            max_speed_angular=20,
            allow_reverse=False,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose)

    async def after_pose3(self):
        await actuators.bottom_grip_mid_open(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_grip_mid(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_grip_mid_close(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_grip_close(self.planner)
        await asyncio.sleep(0.1)
        await actuators.bottom_lift_up(self.planner)
        if BoolSensorEnum.BOTTOM_GRIP_LEFT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state = True
        if BoolSensorEnum.BOTTOM_GRIP_RIGHT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state = True

        # Step back
        back_dist = 250
        diff_x = back_dist * math.cos(math.radians(self.planner.pose_current.O))
        diff_y = back_dist * math.sin(math.radians(self.planner.pose_current.O))

        pose = Pose(
            x=self.planner.pose_current.x - diff_x,
            y=self.planner.pose_current.y - diff_y,
            O=0,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=True,
            bypass_final_orientation=True,
            after_pose_func=self.after_pose4,
        )
        self.poses.append(pose)

    async def after_pose4(self):
        self.plant_supply.enabled = True

    def weight(self) -> float:
        if (
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.TOP_GRIP_RIGHT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state
        ):
            return 0
        return 1000000.0


class PotCaptureAction(Action):
    """
    Action used to capture pots using magnets.
    """

    def __init__(self, planner: "Planner", actions: Actions, pot_supply_id: artifacts.PotSupplyID):
        super().__init__("PotCapture action", planner, actions)
        self.before_action_func = self.before_action
        self.pot_supply = self.game_context.pot_supplies[pot_supply_id]
        self.shift_approach = 335
        self.shift_forward = 160

        match self.pot_supply.angle:
            case -90:
                self.approach_x = self.pot_supply.x
                self.approach_y = -1500 + self.shift_approach
                self.capture_x = self.approach_x
                self.capture_y = self.approach_y - self.shift_forward
            case 90:
                self.approach_x = self.pot_supply.x
                self.approach_y = 1500 - self.shift_approach
                self.capture_x = self.approach_x
                self.capture_y = self.approach_y + self.shift_forward
            case 180:
                self.approach_x = -1000 + self.shift_approach
                self.approach_y = self.pot_supply.y
                self.capture_x = self.approach_x - self.shift_forward
                self.capture_y = self.approach_y

    async def recycle(self):
        await actuators.cart_magnet_off(self.planner)
        await actuators.cart_in(self.planner)
        self.pot_supply.enabled = True
        self.recycled = True

    async def before_action(self):
        self.start_pose = self.planner.pose_current.model_copy()

        pose = Pose(
            x=self.approach_x,
            y=self.approach_y,
            O=self.pot_supply.angle,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=False,
            before_pose_func=self.before_pose1,
            after_pose_func=self.after_pose1,
        )
        self.poses.append(pose)

        # Capture
        pose = Pose(
            x=self.capture_x,
            y=self.capture_y,
            O=self.pot_supply.angle,
            max_speed_linear=5,
            max_speed_angular=5,
            allow_reverse=False,
            bypass_anti_blocking=True,
            timeout_ms=3000,
            after_pose_func=self.after_pose2,
        )
        self.poses.append(pose)

        # Step-back
        pose = Pose(
            x=self.approach_x,
            y=self.approach_y,
            O=self.pot_supply.angle,
            max_speed_linear=10,
            max_speed_angular=10,
            allow_reverse=True,
            after_pose_func=self.after_pose3,
        )
        self.poses.append(pose)

    async def before_pose1(self):
        await asyncio.gather(
            actuators.bottom_grip_close(self.planner),
            actuators.top_grip_close(self.planner),
        )
        await asyncio.gather(
            actuators.top_lift_up(self.planner),
            actuators.bottom_lift_up(self.planner),
        )

    async def after_pose1(self):
        await actuators.cart_out(self.planner)
        await actuators.cart_magnet_on(self.planner)

        self.pot_supply.enabled = False

    async def after_pose2(self):
        await asyncio.sleep(1)

    async def after_pose3(self):
        self.pot_supply.enabled = True
        self.pot_supply.count -= 2
        if BoolSensorEnum.MAGNET_LEFT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state = True
        if BoolSensorEnum.MAGNET_RIGHT in self.game_context.emulated_actuator_states:
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state = True

    def weight(self) -> float:
        if self.pot_supply.count < 5:
            return 0
        if not (
            self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_LEFT].state
            and self.game_context.bool_sensor_states[BoolSensorEnum.BOTTOM_GRIP_RIGHT].state
        ):
            return 0
        if (
            self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_LEFT].state
            or self.game_context.bool_sensor_states[BoolSensorEnum.MAGNET_RIGHT].state
        ):
            return 0

        return 2000000.0


class SolarPanelsAction(Action):
    """
    Activate a solar panel group.
    """

    def __init__(self, planner: "Planner", actions: Actions, solar_panels_id: artifacts.SolarPanelsID):
        super().__init__("SolarPanels action", planner, actions)
        self.solar_panels = self.game_context.solar_panels[solar_panels_id]
        self.before_action_func = self.before_action
        self.shift_x = -215
        self.shift_y = 285

    async def recycle(self):
        await actuators.arm_panel_close(self.planner)
        self.recycled = True

    async def before_action(self):
        self.start_pose = self.planner.pose_current.model_copy()
        if self.game_context.camp.color == Camp.Colors.blue:
            self.shift_y = -self.shift_y

        if self.solar_panels.id == artifacts.SolarPanelsID.Shared:
            self.game_context.pot_supplies[artifacts.PotSupplyID.LocalBottom].enabled = False
            self.game_context.pot_supplies[artifacts.PotSupplyID.LocalBottom].count = 0
            await asyncio.sleep(0.5)

        # Start pose
        self.pose1 = Pose(
            x=self.solar_panels.x - self.shift_x,
            y=self.solar_panels.y - self.shift_y,
            O=90,
            max_speed_linear=66,
            max_speed_angular=66,
            allow_reverse=True,
            after_pose_func=self.after_pose1,
        )

        self.poses.append(self.pose1)

        # End pose
        self.poses.append(
            Pose(
                x=self.solar_panels.x - self.shift_x,
                y=self.solar_panels.y + self.shift_y,
                O=90,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=True,
                after_pose_func=self.after_pose2,
            )
        )

        if self.solar_panels.id == artifacts.SolarPanelsID.Shared:
            # Go back to pose1
            self.poses.append(
                Pose(
                    x=self.pose1.x,
                    y=self.pose1.y,
                    O=self.pose1.O,
                    max_speed_linear=66,
                    max_speed_angular=66,
                    allow_reverse=True,
                )
            )

    async def after_pose1(self):
        await actuators.arm_panel_open(self.planner)
        await asyncio.sleep(1)

    async def after_pose2(self):
        await actuators.arm_panel_close(self.planner)
        await asyncio.sleep(0.5)
        self.game_context.score += 15

    def weight(self) -> float:
        return 2000000.0

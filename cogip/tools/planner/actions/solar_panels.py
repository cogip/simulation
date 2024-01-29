import asyncio
from typing import TYPE_CHECKING

from cogip.models import models
from cogip.tools.camera.detect import solar_panels_positions
from .. import actuators, logger
from ..cameras import get_robot_position, get_solar_panels
from ..pose import Pose
from .actions import Action, Actions

if TYPE_CHECKING:
    from ..planner import Planner
    from ..robot import Robot


class SetRobotPositionAction(Action):
    """
    Use the camera and a table Aruco marker to find the current robot position.
    """
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("SetRobotPosition action", planner, actions)
        self.after_action_func = self.get_position

    async def get_position(self):
        await actuators.right_arm_folded(self.robot.robot_id, self.planner)

        pose = await get_robot_position(self.robot)
        if not pose:
            logger.error("Cannot find table marker and current robot position")
            return

        await actuators.led_on(self.robot.robot_id, self.planner)
        await asyncio.sleep(0.2)
        await actuators.led_off(self.robot.robot_id, self.planner)

        await self.robot.set_pose_start(pose)

        self.actions.append(DiscoverSolarPanelsAction(self.planner, self.actions))

    def weight(self, robot: "Robot") -> float:
        return 1000000.0


class DiscoverSolarPanelsAction(Action):
    """
    Use the camera to find orientation of solar panels.
    """
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__("DiscoverSolarPanel action", planner, actions)
        self.poses.append(
            Pose(
                x=-500,
                y=-1000,
                O=180,
                max_speed_linear=models.SpeedEnum.LOW,
                max_speed_angular=models.SpeedEnum.LOW,
                after_pose_func=self.get_solar_panels,
            )
        )

    async def get_solar_panels(self):
        await asyncio.sleep(2)
        solar_panels = await get_solar_panels(self.robot)
        for panel_id, angle in solar_panels.items():
            # Angle are given for yellow camp only
            log_prefix = f"Solar panel {panel_id}: angle={angle}"
            match angle:
                case angle if -5 <= angle < 20:
                    logger.info(f"{log_prefix}, need activation")
                    self.actions.append(SolarPanelAction(self.planner, self.actions, panel_id, angle))
                case angle if 20 <= angle <= 180:
                    logger.info(f"{log_prefix}, already activated")
                case angle if -179 <= angle <= -160:
                    logger.info(f"{log_prefix}, already activated")
                case _:
                    logger.info(f"{log_prefix}, cannot be activated")

    def weight(self, robot: "Robot") -> float:
        return 900000.0


class SolarPanelAction(Action):
    """
    Activate a solar panel.
    """
    def __init__(self, planner: "Planner", actions: Actions, panel_id: int, angle: float):
        super().__init__("SolarPanelAction action", planner, actions)
        self.panel_id = panel_id
        self.angle = angle
        solar_panel = solar_panels_positions[panel_id]

        robot_y = solar_panel.y - 30

        self.poses.append(
            Pose(
                x=-750,
                y=robot_y,
                O=180,
                max_speed_linear=models.SpeedEnum.LOW,
                max_speed_angular=models.SpeedEnum.LOW,
                after_pose_func=self.extend_arm,
            )
        )

        self.poses.append(
            Pose(
                x=-1000 + self.game_context.properties.robot_width / 2 + 20,
                y=robot_y,
                O=180,
                max_speed_linear=models.SpeedEnum.LOW,
                max_speed_angular=models.SpeedEnum.LOW,
                allow_reverse=False,
            )
        )

        self.poses.append(
            Pose(
                x=-750,
                y=robot_y,
                O=180,
                max_speed_linear=models.SpeedEnum.LOW,
                max_speed_angular=models.SpeedEnum.LOW,
                after_pose_func=self.fold_arm,
            )
        )

    async def extend_arm(self):
        await actuators.right_arm_mid(self.robot.robot_id, self.planner)
        await actuators.led_on(self.robot.robot_id, self.planner)

    async def fold_arm(self):
        await actuators.right_arm_folded(self.robot.robot_id, self.planner)
        await actuators.led_off(self.robot.robot_id, self.planner)

    def weight(self, robot: "Robot") -> float:
        return 800000.0 + self.panel_id


class ParkingAction(Action):
    nb_robots: int = 0

    def __init__(
        self,
        planner: "Planner",
        actions: Actions,
        pose: models.Pose,
    ):
        super().__init__(f"Parking action at ({int(pose.x)}, {int(pose.y)})", planner, actions, interruptable=False)
        self.before_action_func = self.before_action
        self.after_action_func = self.after_action
        self.actions_backup: Actions = []

        self.pose = Pose(
            **pose.model_dump(),
            max_speed_linear=models.SpeedEnum.LOW,
            max_speed_angular=models.SpeedEnum.LOW,
        )
        self.poses = [self.pose]

    def weight(self, robot: "Robot") -> float:
        return 1

    async def before_action(self):
        ParkingAction.nb_robots += 1
        await actuators.right_arm_up(self.robot.robot_id, self.planner)
        await actuators.right_arm_folded(self.robot.robot_id, self.planner)

        if ParkingAction.nb_robots == len(self.planner._robots):
            # Backup actions in the the action is recycled
            self.actions_backup = self.actions[:]

            # Clear remaining actions
            self.actions.clear()

    async def after_action(self):
        self.robot.parked = True
        await self.planner._sio_ns.emit("robot_end", self.robot.robot_id)

    async def recycle(self):
        ParkingAction.nb_robots -= 1
        if self.actions_backup:
            self.actions = self.actions_backup[:]
            self.actions_backup.clear()
        self.recycled = True


class SolarPanelActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(SetRobotPositionAction(planner, self))
        self.append(
            ParkingAction(
                planner,
                self,
                models.Pose(
                    x=-(1000 - 450 + self.game_context.properties.robot_width / 2),
                    y=-(1500 - 450 + self.game_context.properties.robot_width / 2),
                    O=90,
                )
            )
        )

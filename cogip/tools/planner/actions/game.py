import asyncio
import math
from typing import TYPE_CHECKING

# from cogip.models import actuators
from cogip.models import models
from cogip.models.artifacts import CakeLayerPos  # , CakeSlotID
from .. import actuators, cake, cameras, logger
from ..camp import Camp
from ..pose import Pose
from .actions import Action, Actions, WaitAction

if TYPE_CHECKING:
    from ..planner import Planner
    from ..robot import Robot


class LaunchCherriesAction(Action):
    def __init__(
            self,
            planner: "Planner", actions: Actions):
        super().__init__("Launch cherries", planner, actions)
        y = -1000 + 450 - 225 / 2
        if Camp().Colors.green:
            y = -y
        launch_pose = Pose(
            x=225 / 2 + 50, y=y, O=180,
            after_pose_func=self.after_launch_pose
        )
        step_back_pose = Pose(
            x=450 - 225 / 2, y=launch_pose.y, O=launch_pose.O
        )
        self.poses = [launch_pose, step_back_pose]

    def weight(self, robot: "Robot") -> float:
        if robot.robot_id != 1:
            return 0
        return 4000

    async def after_launch_pose(self):
        await actuators.cherry_conveyor_on(self.robot.robot_id, self.planner)
        await asyncio.sleep(6)
        await actuators.cherry_conveyor_off(self.robot.robot_id, self.planner)


# Get cakes actions, one for each slot (12)
class GetCakesAtSlotAction(Action):
    def __init__(
            self,
            planner: "Planner", actions: Actions,
            slot: "cake.CakeSlot"):
        super().__init__(f"Get cakes action at ({int(slot.x)}, {int(slot.y)})", planner, actions)
        self.slot = slot
        self.cake = slot.cake
        self.init_action()

    def init_action(self):
        self.take_pose = Pose(
            x=self.slot.x, y=self.slot.y, O=None, allow_reverse=False,
            max_speed_linear=models.SpeedEnum.NORMAL, max_speed_angular=models.SpeedEnum.NORMAL
        )
        self.take_pose.before_pose_func = self.before_take_pose
        self.take_pose.after_pose_func = self.after_take_pose
        self.poses = [self.take_pose]

    def weight(self, robot: "Robot") -> float:
        if robot.cake is not None:
            return 0
        if self.slot.cake is None:
            return 0
        # cameras.is_cake_in_slot(self.slot.slot_id)
        layer = self.cake.layers.get(CakeLayerPos.BOTTOM)
        if layer is None:
            return 0

        # Compute distance
        dist = math.dist((self.slot.x, self.slot.y), (robot.pose_current.x, robot.pose_current.y))
        # Max distance is 3600, calculate the ratio between 0 and 1000
        dist = (3600 - dist) / 3600 * 1000
        return dist

    async def before_take_pose(self):
        logger.debug(f"Robot {self.robot.robot_id}: cake({int(self.slot.x)}, {int(self.slot.y)}): before_take_pose")
        if cake := self.slot.cake:
            cake.robot = self.robot
        self.planner.update_cake_obstacles(self.robot.robot_id)

        await actuators.central_arm_up(self.robot.robot_id, self.planner)

    async def after_take_pose(self):
        logger.debug(f"Robot {self.robot.robot_id}: cake({int(self.slot.x)}, {int(self.slot.y)}): after_take_pose")
        self.slot.cake.on_table = False
        self.robot.cake = self.slot.cake
        self.slot.cake = None

        duration = await actuators.central_arm_down(self.robot.robot_id, self.planner)
        await asyncio.sleep(duration)

        # Create step back pose
        step_back_distance = 100
        angle = math.radians(self.robot.pose_current.O)
        step_back_pose = Pose(
            x=self.robot.pose_current.x - step_back_distance * math.cos(angle),
            y=self.robot.pose_current.y - step_back_distance * math.sin(angle),
            O=self.robot.pose_current.O, allow_reverse=True,
            max_speed_linear=models.SpeedEnum.NORMAL, max_speed_angular=models.SpeedEnum.NORMAL
        )
        self.poses.append(step_back_pose)

    async def recycle(self):
        self.slot.cake = self.cake
        self.slot.cake.robot = None
        self.planner.update_cake_obstacles(self.robot.robot_id)
        self.init_action()
        await super().recycle()


class DropCakeAction(Action):
    def __init__(
            self,
            planner: "Planner", actions: Actions,
            slot: "cake.DropSlot", angle: int, weight: int, robot_id):
        super().__init__(
            f"Drop cake action at ({int(slot.x)}, {int(slot.y)})", planner, actions
        )
        self.game_context.drop_slots.append(slot)
        self.slot = slot
        self.angle = angle
        self._weight = weight
        self.robot_id = robot_id
        self.cherry_dropped = False
        self.init_action()

    def init_action(self):
        self.drop_pose = Pose(
            x=self.slot.x, y=self.slot.y, O=self.angle, allow_reverse=True,
            max_speed_linear=models.SpeedEnum.NORMAL, max_speed_angular=models.SpeedEnum.NORMAL,
            after_pose_func=self.after_drop_pose
        )
        if self.slot.x > self.game_context.table.x_max / 2:
            self.drop_pose.x -= 100
        else:
            self.drop_pose.x += 100
        self.poses = [self.drop_pose]

    def weight(self, robot: "Robot") -> float:
        if robot.robot_id != self.robot_id:
            return 0
        if robot.cake is None:
            return 0
        return self._weight

    async def after_drop_pose(self):
        logger.debug(f"Robot {self.robot.robot_id}: cake({int(self.slot.x)}, {int(self.slot.y)}): after_drop_pose")

        if self.robot.nb_cherries:
            duration = await actuators.action_deliver_on_cake(self.robot.robot_id, self.planner)
            self.cherry_dropped = True
            self.robot.nb_cherries -= 1
        else:
            duration = await actuators.central_arm_up(self.robot.robot_id, self.planner)
        await asyncio.sleep(duration)

        # Create step back pose
        step_back_distance = 100
        angle = math.radians(self.robot.pose_current.O)
        step_back_pose = Pose(
            x=self.robot.pose_current.x - step_back_distance * math.cos(angle),
            y=self.robot.pose_current.y - step_back_distance * math.sin(angle),
            O=self.robot.pose_current.O, allow_reverse=True,
            max_speed_linear=models.SpeedEnum.NORMAL, max_speed_angular=models.SpeedEnum.NORMAL,
            after_pose_func=self.after_step_back
        )
        self.drop_pose.after_pose_func = self.after_drop_pose

        self.poses.append(step_back_pose)

    async def after_step_back(self):
        logger.debug(f"Robot {self.robot.robot_id}: cake({int(self.slot.x)}, {int(self.slot.y)}): after_drop_pose")
        self.robot.cake.on_table = True
        self.slot.cake = self.robot.cake
        self.slot.cake.x = self.slot.x
        self.slot.cake.y = self.slot.y
        self.robot.cake = None
        self.planner.update_cake_obstacles()
        self.game_context.score += 3

        if self.cherry_dropped:
            has_cherry = await cameras.is_cherry_on_cake(self.robot.robot_id)
            if has_cherry:
                self.game_context.score += 3

    async def recycle(self):
        if self.slot.cake:
            self.slot.cake.robot = None
        self.slot.cake = None
        self.planner.update_cake_obstacles(self.robot.robot_id)
        self.init_action()
        await super().recycle()


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

        self.game_context.create_cakes()

        self.append(LaunchCherriesAction(planner, self))

        slots_to_create = self.game_context.cake_slots.values()
        # slots_to_create = [
        #     self.game_context.cake_slots[CakeSlotID.GREEN_FRONT_SPONGE],
        #     self.game_context.cake_slots[CakeSlotID.GREEN_FRONT_SPONGE],
        # ]
        for slot in slots_to_create:
            self.append(GetCakesAtSlotAction(planner, self, slot))

        # Back platter
        self.append(DropCakeAction(
            planner, self,
            slot=cake.DropSlot(160, Camp().adapt_y(-800)),
            angle=-180,
            weight=500,
            robot_id=1
        ))
        self.append(DropCakeAction(
            planner, self,
            slot=cake.DropSlot(160, Camp().adapt_y(-600)),
            angle=-180,
            weight=400,
            robot_id=1
        ))
        self.append(DropCakeAction(
            planner, self,
            slot=cake.DropSlot(380, Camp().adapt_y(-800)),
            angle=-180,
            weight=300,
            robot_id=1
        ))

        # Front corner plate
        self.append(DropCakeAction(
            planner, self,
            slot=cake.DropSlot(self.game_context.table.x_max - 160, Camp().adapt_y(800)),
            angle=0,
            weight=500,
            robot_id=2
        ))
        self.append(DropCakeAction(
            planner, self,
            slot=cake.DropSlot(self.game_context.table.x_max - 160, Camp().adapt_y(600)),
            angle=0,
            weight=400,
            robot_id=2
        ))
        self.append(DropCakeAction(
            planner, self,
            slot=cake.DropSlot(self.game_context.table.x_max - 380, Camp().adapt_y(800)),
            angle=0,
            weight=300,
            robot_id=2
        ))

        ParkingAction.nb_robots = 0
        if Camp().color == Camp.Colors.blue:
            self.append(ParkingAction(planner, self, models.Pose(x=1500 + 150, y=-1000 + 450, O=None)))
            self.append(ParkingAction(planner, self, models.Pose(x=1500 + 150 + 450, y=-1000 + 450, O=None)))
        else:
            self.append(ParkingAction(planner, self, models.Pose(x=1500 - 150, y=-1000 + 450, O=None)))
            self.append(ParkingAction(planner, self, models.Pose(x=1500 - 150 - 450, y=-1000 + 450, O=None)))

        self.planner._start_positions[1] = 1
        self.planner._start_positions[2] = 4

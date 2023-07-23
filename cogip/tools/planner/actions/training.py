import asyncio
import math
from typing import TYPE_CHECKING

# from cogip.models import actuators
from cogip.models import models
from cogip.models.artifacts import CakeLayerID, CakeLayerPos
from .. import actuators, cake, cameras, table, logger
from ..camp import Camp
from ..pose import Pose
from .actions import Action, Actions, WaitAction

if TYPE_CHECKING:
    from ..planner import Planner
    from ..robot import Robot


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
        layer = self.cake.layers.get(CakeLayerPos.BOTTOM)
        if layer is None:
            return 0
        return 900

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
            slot: "cake.DropSlot", angle: int, weight: int):
        super().__init__(f"Drop cake action at ({int(slot.x)}, {int(slot.y)})", planner, actions)
        self.game_context.drop_slots.append(slot)
        self.slot = slot
        self.angle = angle
        self._weight = weight
        self.cherry_dropped = False
        self.init_action()

    def init_action(self):
        self.drop_pose = Pose(
            x=self.slot.x, y=self.slot.y, O=self.angle, allow_reverse=False,
            max_speed_linear=models.SpeedEnum.NORMAL, max_speed_angular=models.SpeedEnum.NORMAL,
            after_pose_func=self.after_drop_pose
        )
        if self.slot.x > self.game_context.table.x_max / 2:
            self.drop_pose.x -= 100
        else:
            self.drop_pose.x += 100
        self.poses = [self.drop_pose]

    def weight(self, robot: "Robot") -> float:
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


class FinalAction(Action):
    def __init__(
            self,
            planner: "Planner", actions: Actions,
            pose: models.Pose):
        super().__init__(f"Final action at ({int(pose.x)}, {int(pose.y)})", planner, actions)
        self.pose = Pose(**pose.dict(), after_pose_func=self.after_final)
        self.poses = [self.pose]

    def weight(self, robot: "Robot") -> float:
        if self.game_context.countdown > 10:
            return 0
        return 100000

    async def after_final(self):
        self.actions.clear()

        self.game_context.score += 15

        await actuators.led_on(self.robot.robot_id, self.planner)
        self.game_context.score += 5

        await self.planner._sio_ns.emit("score", self.game_context.score)


class TrainingActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.append(WaitAction(planner, self))

        cakes_to_create = [
            CakeLayerID.BLUE_FRONT_ICING_BOTTOM, CakeLayerID.BLUE_FRONT_ICING_MIDDLE, CakeLayerID.BLUE_FRONT_ICING_TOP,
            CakeLayerID.BLUE_FRONT_CREAM_BOTTOM, CakeLayerID.BLUE_FRONT_CREAM_MIDDLE, CakeLayerID.BLUE_FRONT_CREAM_TOP,
            CakeLayerID.BLUE_FRONT_SPONGE_BOTTOM, CakeLayerID.BLUE_FRONT_SPONGE_MIDDLE, CakeLayerID.BLUE_FRONT_SPONGE_TOP,
        ]
        self.game_context.create_cakes(cakes_to_create)

        for slot in self.game_context.cake_slots.values():
            self.append(GetCakesAtSlotAction(planner, self, slot))

        # Back platter
        # self.append(DropCakeAction(
        #     planner,
        #     slot=cake.DropSlot(130, -850),
        #     angle=-180,
        #     weight=500
        # ))
        # self.append(DropCakeAction(
        #     planner,
        #     slot=cake.DropSlot(130, -610),
        #     angle=-180,
        #     weight=400
        # ))
        # self.append(DropCakeAction(
        #     planner,
        #     slot=cake.DropSlot(360, -850),
        #     angle=-180,
        #     weight=300
        # ))

        # Front corner plate
        self.append(DropCakeAction(
            planner, self,
            slot=cake.DropSlot(self.game_context.table.x_max - 160, Camp().adapt_y(800)),
            angle=0,
            weight=500
        ))
        self.append(DropCakeAction(
            planner, self,
            slot=cake.DropSlot(self.game_context.table.x_max - 160, Camp().adapt_y(530)),
            angle=0,
            weight=400
        ))
        self.append(DropCakeAction(
            planner, self,
            slot=cake.DropSlot(self.game_context.table.x_max - 380, Camp().adapt_y(800)),
            angle=0,
            weight=300
        ))

        self.append(FinalAction(planner, self, models.Pose(x=1875, y=-770, O=-180)))

        if self.game_context._table == table.TableEnum.Training:
            self.planner._start_positions[1] = 2
            self.planner._start_positions[2] = 3
        else:
            self.planner._start_positions[1] = 1
            self.planner._start_positions[2] = 4

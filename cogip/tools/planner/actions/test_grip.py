from typing import TYPE_CHECKING

from cogip.models import artifacts
from .. import actuators
from ..pose import Pose
from . import base_actions
from .actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class GripAction(base_actions.GripAction):
    def __init__(self, planner: "Planner", actions: Actions, plant_supply_id: artifacts.PlantSupplyID):
        super().__init__(planner, actions, plant_supply_id)

    async def after_pose4(self):
        await super().after_pose4()
        self.poses.append(
            Pose(
                x=self.start_pose.x,
                y=self.start_pose.y,
                O=self.start_pose.O,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=True,
                after_pose_func=self.after_pose5,
            )
        )

    async def after_pose5(self):
        await actuators.top_grip_open(self.planner)
        await actuators.bottom_grip_open(self.planner)


class TestGripActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(GripAction(planner, self, artifacts.PlantSupplyID.LocalBottom))

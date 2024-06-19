import asyncio
from typing import TYPE_CHECKING

from cogip.models import artifacts
from .. import actuators
from ..pose import Pose
from . import base_actions
from .actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class DropInPlanterAction(base_actions.DropInPlanterAction):
    async def after_pose2(self):
        await super().after_pose2()
        self.poses.append(
            Pose(
                x=self.start_pose.x,
                y=self.start_pose.y,
                O=self.start_pose.O,
                max_speed_linear=66,
                max_speed_angular=66,
                allow_reverse=True,
            )
        )

    def weight(self) -> float:
        return 1000000.0


class TestPlanterActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        drop_action = DropInPlanterAction(planner, self, artifacts.PlanterID.Test)
        drop_action.before_action_func = self.setup_actuators
        self.append(drop_action)

    async def setup_actuators(self):
        await asyncio.gather(
            actuators.bottom_grip_close(self.planner),
            actuators.top_grip_close(self.planner),
            actuators.cart_in(self.planner),
            asyncio.sleep(0.2),
        )
        await actuators.top_lift_up(self.planner)
        await asyncio.sleep(0.2)
        await actuators.bottom_lift_up(self.planner)
        await asyncio.sleep(1)

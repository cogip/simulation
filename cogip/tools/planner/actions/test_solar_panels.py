from typing import TYPE_CHECKING

from cogip.models import artifacts
from ..pose import Pose
from . import base_actions
from .actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class SolarPanelsAction(base_actions.SolarPanelsAction):
    def __init__(self, planner: "Planner", actions: Actions, solar_panels_id: artifacts.SolarPanelsID):
        super().__init__(planner, actions, solar_panels_id)

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


class TestSolarPanelsActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(SolarPanelsAction(planner, self, artifacts.SolarPanelsID.Local))

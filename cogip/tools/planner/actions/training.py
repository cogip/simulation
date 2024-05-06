from typing import TYPE_CHECKING

from cogip.models import artifacts, models
from .. import table
from ..positions import StartPosition
from . import base_actions
from .actions import Actions, WaitAction

if TYPE_CHECKING:
    from ..planner import Planner


class TrainingActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        if self.game_context._table == table.TableEnum.Training:
            parking_pose = models.Pose(x=-1000 + 450, y=-1500 + 450, O=0)
            planter_id = artifacts.PlanterID.Test
        else:
            parking_pose = models.Pose(x=0, y=1500 + 450, O=0)
            planter_id = artifacts.PlanterID.Top

        self.planner.start_position = StartPosition.Bottom
        self.append(base_actions.SolarPanelsAction(planner, self, artifacts.SolarPanelsID.Local))
        self.append(base_actions.GripAction(planner, self, artifacts.PlantSupplyID.LocalBottom))
        self.append(base_actions.PotCaptureAction(planner, self, artifacts.PotSupplyID.LocalMiddle))
        self.append(base_actions.DropInDropoffZoneAction(planner, self, artifacts.DropoffZoneID.Bottom, 2))
        self.append(base_actions.DropInPlanterAction(planner, self, planter_id))
        self.append(WaitAction(planner, self))
        self.append(base_actions.ParkingAction(planner, self, parking_pose))

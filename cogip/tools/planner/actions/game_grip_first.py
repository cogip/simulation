from typing import TYPE_CHECKING

from cogip.models import artifacts, models
from .. import logger, table
from . import base_actions
from .actions import Actions, WaitAction

if TYPE_CHECKING:
    from ..planner import Planner


default_weights = {
    "SolarPanelsAction_Local": 8000000.0,
    "SolarPanelsAction_Shared": 7000000.0,
    "GripAction_LocalBottom": 9000000.0,
    "GripAction_LocalTop": 6700000.0,
    "GripAction_CenterBottom": 6600000.0,
    "PotCaptureAction_LocalMiddle": 5900000.0,
    "PotCaptureAction_LocalTop": 5500000.0,
    "DropInDropoffZoneAction_Bottom": 4500000.0,
    "DropInDropoffZoneAction_Top": 4900000.0,
    "DropInPlanterAction_Top": 3500000.0,
    "DropInPlanterAction_LocalSide": 3900000.0,
    "DropInPlanterAction_Test": 1000000.0,
}


class DefaultWeightAction:
    def default_weight(self) -> float:
        weight = default_weights.get(self.__class__.__name__)
        if weight is None:
            logger.warning(f"Missing  default weight for {self.__class__.__name__}")
            weight = 1000000.0
        return weight


class SolarPanelsAction_Local(base_actions.SolarPanelsAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.SolarPanelsID.Local)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class SolarPanelsAction_Shared(base_actions.SolarPanelsAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.SolarPanelsID.Shared)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class GripAction_LocalBottom(base_actions.GripAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.PlantSupplyID.LocalBottom)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class GripAction_LocalTop(base_actions.GripAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.PlantSupplyID.LocalTop)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class GripAction_CenterBottom(base_actions.GripAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.PlantSupplyID.CenterBottom)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class PotCaptureAction_LocalMiddle(base_actions.PotCaptureAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.PotSupplyID.LocalMiddle)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class PotCaptureAction_LocalTop(base_actions.PotCaptureAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.PotSupplyID.LocalTop)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class DropInDropoffZoneAction_Bottom(base_actions.DropInDropoffZoneAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions, slot: int):
        super().__init__(planner, actions, artifacts.DropoffZoneID.Bottom, slot)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class DropInDropoffZoneAction_Top(base_actions.DropInDropoffZoneAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions, slot: int):
        super().__init__(planner, actions, artifacts.DropoffZoneID.Top, slot)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class DropInPlanterAction_Top(base_actions.DropInPlanterAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.PlanterID.Top)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class DropInPlanterAction_LocalSide(base_actions.DropInPlanterAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.PlanterID.LocalSide)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class DropInPlanterAction_Test(base_actions.DropInPlanterAction, DefaultWeightAction):
    def __init__(self, planner: "Planner", actions: Actions):
        super().__init__(planner, actions, artifacts.PlanterID.Test)

    def weight(self) -> float:
        return 0 if super().weight() == 0 else self.default_weight()


class GameGripFirstActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        if self.game_context._table == table.TableEnum.Training:
            parking_pose = models.Pose(x=-1000 + 450, y=-1500 + 450, O=90)
            self.append(DropInDropoffZoneAction_Bottom(planner, self, 2))
            self.append(PotCaptureAction_LocalMiddle(planner, self))
            self.append(DropInPlanterAction_Test(planner, self))
        else:
            parking_pose = models.Pose(x=0, y=1500 - 450, O=90)
            self.append(DropInDropoffZoneAction_Top(planner, self, 2))
            self.append(PotCaptureAction_LocalTop(planner, self))
            self.append(DropInPlanterAction_Top(planner, self))

        self.append(SolarPanelsAction_Local(planner, self))
        self.append(GripAction_LocalBottom(planner, self))
        self.append(WaitAction(planner, self))
        self.append(base_actions.ParkingAction(planner, self, parking_pose))

        if self.game_context._table == table.TableEnum.Game:
            self.append(SolarPanelsAction_Shared(planner, self))
            self.append(GripAction_LocalTop(planner, self))
            self.append(DropInPlanterAction_LocalSide(planner, self))

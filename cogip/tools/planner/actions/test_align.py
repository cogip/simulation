from typing import TYPE_CHECKING

from cogip.tools.planner.actions import base_actions
from cogip.tools.planner.actions.actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class AlignAction(base_actions.AlignAction):
    pass


class TestAlignActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(AlignAction(planner, self))

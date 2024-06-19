from typing import TYPE_CHECKING

from . import base_actions
from .actions import Actions

if TYPE_CHECKING:
    from ..planner import Planner


class AlignAction(base_actions.AlignAction):
    pass


class TestAlignActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)
        self.append(AlignAction(planner, self))

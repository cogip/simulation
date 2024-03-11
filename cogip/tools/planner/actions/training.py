from typing import TYPE_CHECKING

from cogip.models import models
from .. import actuators, table
from ..pose import Pose
from .actions import Action, Actions, WaitAction

if TYPE_CHECKING:
    from ..planner import Planner


class FinalAction(Action):
    def __init__(self, planner: "Planner", actions: Actions, pose: models.Pose):
        super().__init__(f"Final action at ({int(pose.x)}, {int(pose.y)})", planner, actions)
        self.pose = Pose(**pose.model_dump(), after_pose_func=self.after_final)
        self.poses = [self.pose]

    def weight(self) -> float:
        if self.game_context.countdown > 10:
            return 0
        return 100000

    async def after_final(self):
        self.actions.clear()

        self.game_context.score += 15

        await actuators.led_on(self.planner)
        self.game_context.score += 5

        await self.planner.sio_ns.emit("score", self.game_context.score)


class TrainingActions(Actions):
    def __init__(self, planner: "Planner"):
        super().__init__(planner)

        self.planner.start_position = 2
        self.append(WaitAction(planner, self))
        self.append(FinalAction(planner, self, models.Pose(x=-500, y=-500, O=180)))

        if self.game_context._table != table.TableEnum.Training:
            self.planner.start_position = 1
            self.append(WaitAction(planner, self))
            self.append(FinalAction(planner, self, models.Pose(x=-500, y=500, O=180)))

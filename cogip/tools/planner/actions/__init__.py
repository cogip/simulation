from .actions import Actions
from .approval import ApprovalActions
from .game import GameActions
from .back_and_forth import BackAndForthActions
from .speed_test import SpeedTestActions
from .training import TrainingActions
from .just_move import JustMoveActions
from ..strategy import Strategy

action_classes: dict[Strategy, Actions] = {
    Strategy.Approval: ApprovalActions,
    Strategy.Game: GameActions,
    Strategy.BackAndForth: BackAndForthActions,
    Strategy.AngularSpeedTest: SpeedTestActions,
    Strategy.LinearSpeedTest: SpeedTestActions,
    Strategy.Training: TrainingActions,
    Strategy.JustMove: JustMoveActions
}

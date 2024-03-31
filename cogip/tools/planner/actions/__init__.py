from ..strategy import Strategy
from .actions import Actions
from .align_test import AlignTestActions
from .approval import ApprovalActions
from .back_and_forth import BackAndForthActions
from .camera_calibration import CameraCalibrationActions
from .game import GameActions
from .grip_test import GripTestActions
from .position_test import AngularPositionTestActions, LinearPositionTestActions
from .pot_capture_test import PotCaptureTestActions
from .solar_panels import SolarPanelActions
from .speed_test import SpeedTestActions
from .training import TrainingActions

action_classes: dict[Strategy, Actions] = {
    Strategy.Approval: ApprovalActions,
    Strategy.Game: GameActions,
    Strategy.BackAndForth: BackAndForthActions,
    Strategy.AngularSpeedTest: SpeedTestActions,
    Strategy.LinearSpeedTest: SpeedTestActions,
    Strategy.AngularPositionTest: AngularPositionTestActions,
    Strategy.LinearPositionTest: LinearPositionTestActions,
    Strategy.Training: TrainingActions,
    Strategy.CameraCalibration: CameraCalibrationActions,
    Strategy.SolarPanel: SolarPanelActions,
    Strategy.AlignTest: AlignTestActions,
    Strategy.GripTest: GripTestActions,
    Strategy.PotCaptureTest: PotCaptureTestActions,
}

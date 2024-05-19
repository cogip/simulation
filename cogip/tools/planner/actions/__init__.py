from ..strategy import Strategy
from .actions import Actions
from .approval import ApprovalActions
from .back_and_forth import BackAndForthActions
from .camera_calibration import CameraCalibrationActions
from .game import GameActions
from .position_test import AngularPositionTestActions, LinearPositionTestActions
from .solar_panels import SolarPanelActions
from .speed_test import SpeedTestActions
from .test_align import TestAlignActions
from .test_grip import TestGripActions
from .test_pot_capture import TestPotCaptureActions
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
    Strategy.TestAlign: TestAlignActions,
    Strategy.TestGrip: TestGripActions,
    Strategy.TestPotCapture: TestPotCaptureActions,
}

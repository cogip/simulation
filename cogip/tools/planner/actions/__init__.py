from ..strategy import Strategy
from .actions import Actions
from .back_and_forth import BackAndForthActions
from .camera_calibration import CameraCalibrationActions
from .game_grip_first import GameGripFirstActions
from .game_solar_first import GameSolarFirstActions
from .pami import Pami2Actions, Pami3Actions, Pami4Actions
from .position_test import AngularPositionTestActions, LinearPositionTestActions
from .solar_panels import SolarPanelActions
from .speed_test import SpeedTestActions
from .test_align import TestAlignActions
from .test_dropoff import TestDropoffActions
from .test_grip import TestGripActions
from .test_planters import TestPlanterActions
from .test_pot_capture import TestPotCaptureActions
from .test_solar_panels import TestSolarPanelsActions

action_classes: dict[Strategy, Actions] = {
    Strategy.GameGripFirst: GameGripFirstActions,
    Strategy.GameSolarFirst: GameSolarFirstActions,
    Strategy.BackAndForth: BackAndForthActions,
    Strategy.AngularSpeedTest: SpeedTestActions,
    Strategy.LinearSpeedTest: SpeedTestActions,
    Strategy.AngularPositionTest: AngularPositionTestActions,
    Strategy.LinearPositionTest: LinearPositionTestActions,
    Strategy.CameraCalibration: CameraCalibrationActions,
    Strategy.SolarPanel: SolarPanelActions,
    Strategy.TestAlign: TestAlignActions,
    Strategy.TestGrip: TestGripActions,
    Strategy.TestPotCapture: TestPotCaptureActions,
    Strategy.TestSolarPanels: TestSolarPanelsActions,
    Strategy.TestDropoff: TestDropoffActions,
    Strategy.TestPlanter: TestPlanterActions,
    Strategy.PAMI2: Pami2Actions,
    Strategy.PAMI3: Pami3Actions,
    Strategy.PAMI4: Pami4Actions,
}

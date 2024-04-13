from cogip.tools.copilot.controller import ControllerEnum
from cogip.utils.singleton import Singleton
from .avoidance.avoidance import AvoidanceStrategy
from .camp import Camp
from .pose import AdaptedPose, Pose
from .positions import StartPosition
from .properties import Properties
from .strategy import Strategy
from .table import Table, TableEnum, tables


class GameContext(metaclass=Singleton):
    """
    A class recording the current game context.
    """

    game_duration: int = 100
    minimum_score: int = 1 + 5

    def __init__(self):
        self.properties = Properties()
        self.camp = Camp()
        self.strategy = Strategy.LinearPositionTest
        self._table = TableEnum.Training
        self.avoidance_strategy = AvoidanceStrategy.VisibilityRoadMapQuadPid
        self.playing: bool = False
        self.score: int = self.minimum_score
        self.countdown: int = self.game_duration

    @property
    def table(self) -> Table:
        """
        Selected table.
        """
        return tables[self._table]

    @table.setter
    def table(self, new_table: TableEnum):
        self._table = new_table

    def reset(self):
        """
        Reset the context.
        """
        self.playing = False
        self.score = self.minimum_score
        self.countdown = self.game_duration

    @property
    def default_controller(self) -> ControllerEnum:
        match self.strategy:
            case Strategy.AngularSpeedTest:
                return ControllerEnum.ANGULAR_SPEED_TEST
            case Strategy.LinearSpeedTest:
                return ControllerEnum.LINEAR_SPEED_TEST
            case _:
                return ControllerEnum.QUADPID

    def get_start_pose(self, n: int) -> Pose | None:
        """
        Define the possible start positions.
        Default positions for yellow camp.
        """
        match n:
            case StartPosition.Top:
                return AdaptedPose(
                    x=1000 - 450 + self.properties.robot_width / 2,
                    y=-(1500 - 450 + self.properties.robot_length / 2),
                    O=90,
                )
            case StartPosition.Bottom:
                return AdaptedPose(
                    x=-(1000 - 450 + self.properties.robot_width / 2),
                    y=-(1500 - 450 + self.properties.robot_length / 2),
                    O=90,
                )
            case StartPosition.Opposite:
                return AdaptedPose(
                    x=-450 / 2 + self.properties.robot_width / 2,
                    y=1500 - 450 + self.properties.robot_width / 2,
                    O=-90,
                )
            case StartPosition.PAMI1:
                return AdaptedPose(
                    x=1000 - 150 + self.properties.robot_length / 2,
                    y=-self.properties.robot_width / 2,
                    O=180,
                )
            case StartPosition.PAMI2:
                return AdaptedPose(
                    x=1000 - 150 + self.properties.robot_length / 2,
                    y=-450 / 2,
                    O=180,
                )
            case StartPosition.PAMI3:
                return AdaptedPose(
                    x=1000 - 150 + self.properties.robot_length / 2,
                    y=-(450 - self.properties.robot_width / 2),
                    O=180,
                )
            case _:
                return AdaptedPose()

    def get_available_start_poses(self) -> list[StartPosition]:
        """
        Get start poses available depending on camp and table.
        """
        start_pose_indices = []
        for p in StartPosition:
            pose = self.get_start_pose(p)
            if self.table.contains(pose):
                start_pose_indices.append(p)
        return start_pose_indices

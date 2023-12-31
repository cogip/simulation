from cogip.tools.copilot.controller import ControllerEnum
from cogip.utils.singleton import Singleton
from .camp import Camp
from .pose import AdaptedPose, Pose
from .properties import Properties
from .table import Table, TableEnum, tables
from .strategy import Strategy
from .avoidance.avoidance import AvoidanceStrategy


class GameContext(metaclass=Singleton):
    """
    A class recording the current game context.
    """
    game_duration: int = 100
    minimum_score: int = 1 + 5

    def __init__(self):
        self.properties = Properties()
        self.camp = Camp()
        self._strategy = Strategy.BackAndForth
        self._table = TableEnum.Game
        self._avoidance_strategy = AvoidanceStrategy.VisibilityRoadMapQuadPid
        self.playing: bool = False
        self.score: int = self.minimum_score
        self.countdown: int = self.game_duration

    @property
    def strategy(self) -> Strategy:
        """
        Selected strategy.
        """
        return self._strategy

    @property
    def table(self) -> Table:
        """
        Selected table.
        """
        return tables[self._table]

    @table.setter
    def table(self, new_table: TableEnum):
        self._table = new_table

    @strategy.setter
    def strategy(self, s: Strategy):
        self._strategy = s
        self.reset()

    @property
    def avoidance_strategy(self) -> AvoidanceStrategy:
        """
        Selected avoidance strategy.
        """
        return self._avoidance_strategy

    @avoidance_strategy.setter
    def avoidance_strategy(self, s: AvoidanceStrategy):
        self._avoidance_strategy = s
        self.reset()

    def reset(self):
        """
        Reset the context.
        """
        self.playing = False
        self.score = self.minimum_score
        self.countdown = self.game_duration

    @property
    def default_controller(self) -> ControllerEnum:
        match self._strategy:
            case Strategy.AngularSpeedTest:
                return ControllerEnum.ANGULAR_SPEED_TEST
            case Strategy.LinearSpeedTest:
                return ControllerEnum.LINEAR_SPEED_TEST
            case _:
                return ControllerEnum.QUADPID

    def get_start_pose(self, n: int) -> Pose | None:
        """
        Define the possible start positions.
        Default positions for blue camp.
        """
        match n:
            case 1:  # Top left
                return AdaptedPose(
                    x=1000 - 450 + self.properties.robot_width / 2,
                    y=1500 - 450 + self.properties.robot_width / 2,
                    O=-90
                )
            case 2:  # Bottom left
                return AdaptedPose(
                    x=-(1000 - 450 + self.properties.robot_width / 2),
                    y=1500 - 450 + self.properties.robot_width / 2,
                    O=-90
                )
            case 3:  # Middle right
                return AdaptedPose(
                    x=self.properties.robot_width / 2,
                    y=-(1500 - 450 + self.properties.robot_width / 2),
                    O=90
                )

    def get_available_start_poses(self) -> list[int]:
        """
        Get start poses available depending on camp and table.
        """
        start_pose_indices = []
        for i in range(1, 4):
            pose = self.get_start_pose(i)
            if self.table.contains(pose):
                start_pose_indices.append(i)

        return start_pose_indices

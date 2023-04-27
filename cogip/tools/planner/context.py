from cogip.entities.artifacts import default_cake_layers
from cogip.models.models import CakeLayer, CakeLayerID
from cogip.tools.copilot.controller import ControllerEnum
from cogip.utils.singleton import Singleton
from .camp import Camp
from .cake import Cake, CakeSlot
from .pose import AdaptedPose, Pose
from .table import Table, TableEnum, tables
from .strategy import Strategy
from .avoidance.avoidance import AvoidanceStrategy


class GameContext(metaclass=Singleton):
    """
    A class recording the current game context.
    """
    def __init__(self):
        self.camp = Camp()
        self._strategy = Strategy.BackAndForth
        self._table = TableEnum.Game
        self._avoidance_strategy = AvoidanceStrategy.VisibilityRoadMapQuadPid
        self.playing: bool = False
        self.score: int = 0
        self.cake_layers: dict[CakeLayerID, CakeLayer] = {}
        self.cakes: list[Cake] = []
        self.cake_slots: list[CakeSlot] = []
        self.create_cakes()

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
        self.score = 0
        self.create_cakes()

    @property
    def default_controller(self) -> ControllerEnum:
        match self._strategy:
            case Strategy.AngularSpeedTest:
                return ControllerEnum.ANGULAR_SPEED_TEST
            case Strategy.LinearSpeedTest:
                return ControllerEnum.LINEAR_SPEED_TEST
            case _:
                return ControllerEnum.QUADPID

    @classmethod
    def get_start_pose(cls, n: int) -> Pose | None:
        """
        Define the possible start positions.
        """
        match n:
            case 1:
                return AdaptedPose(x=225, y=-775, O=0)
            case 2:
                return AdaptedPose(x=1875, y=-775, O=90)
            case 3:
                return AdaptedPose(x=2775, y=-275, O=180)
            case 4:
                return AdaptedPose(x=2775, y=775, O=180)
            case 5:
                return AdaptedPose(x=1125, y=775, O=-90)
            case _:
                return None

    def get_available_start_poses(self) -> list[int]:
        """
        Get start poses available depending on camp and table.
        """
        start_pose_indices = []
        for i in range(1, 6):
            pose = GameContext.get_start_pose(i)
            if self.table.contains(pose):
                start_pose_indices.append(i)

        return start_pose_indices

    def create_cakes(self):
        table = self.table
        self.cakes = []
        self.cake_slots = []
        for cake_layer_id, values in default_cake_layers.items():
            x, y, pos, kind = values
            if x < table.x_min or \
               x > table.x_max or \
               y < table.y_min or \
               y > table.y_max:
                continue

            layer = CakeLayer(
                id=cake_layer_id,
                x=values[0],
                y=values[1],
                pos=values[2],
                kind=values[3]
            )
            self.cake_layers[cake_layer_id] = layer

            cake: Cake | None = None
            for cake in self.cakes:
                if (cake.x, cake.y) == (layer.x, layer.y):
                    break
                cake = None
            if cake is None:
                cake = Cake(x=layer.x, y=layer.y)
                self.cakes.append(cake)
                self.cake_slots.append(CakeSlot(layer.x, layer.y, layer.kind, cake))

            cake.layers[layer.pos] = layer

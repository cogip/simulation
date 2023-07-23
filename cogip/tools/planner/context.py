from cogip.models.artifacts import default_cake_layers, CakeLayer, CakeLayerID, CakeSlotID
from cogip.tools.copilot.controller import ControllerEnum
from cogip.utils.singleton import Singleton
from .camp import Camp
from .cake import Cake, CakeSlot, DropSlot
from .pose import AdaptedPose, Pose
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
        self.camp = Camp()
        self._strategy = Strategy.BackAndForth
        self._table = TableEnum.Game
        self._avoidance_strategy = AvoidanceStrategy.VisibilityRoadMapQuadPid
        self.playing: bool = False
        self.score: int = self.minimum_score
        self.cake_layers: dict[CakeLayerID, CakeLayer] = {}
        self.cakes: list[Cake] = []
        self.cake_slots: dict[CakeSlotID, CakeSlot] = {}
        self.drop_slots: list[DropSlot] = []
        self.create_cakes()
        self.countdown: int = self.game_duration
        self.nb_cherries: int = 0

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
        self.create_cakes()
        self.countdown = self.game_duration
        self.nb_cherries = 0

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
                return AdaptedPose(x=450 - 225 / 2, y=-1000 + 450 - 225 / 2, O=180)
            case 2:
                return AdaptedPose(x=3000 - 450 - 125 - 200 - 125 - 225 / 2, y=-1000 + 450 - 225 / 2, O=90)
            case 3:
                return AdaptedPose(x=3000 - 450 + 225 / 2, y=-1000 + 450 + 50 + 225 / 2, O=180)
            case 4:
                return AdaptedPose(x=3000 - 450 + 225 / 2, y=1000 - 450 + 225 / 2, O=180)
            case 5:
                return AdaptedPose(x=450 + 125 + 200 + 125 - 225 / 2, y=1000 - 450 + 225 / 2, O=-90)

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

    def create_cakes(self, layers: list[CakeLayerID] = []):
        table = self.table
        self.cakes = []
        self.cake_layers = {}
        self.cake_slots = {}

        if not layers:
            layers = list(default_cake_layers.keys())

        cakes_to_create = list(default_cake_layers.keys())
        for cake_layer_id in cakes_to_create:
            x, y, kind, pos = default_cake_layers[cake_layer_id]
            if x < table.x_min or \
               x > table.x_max or \
               y < table.y_min or \
               y > table.y_max:
                continue

            layer = CakeLayer(
                id=cake_layer_id,
                x=x,
                y=y,
                pos=pos,
                kind=kind
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
                match cake_layer_id:
                    case CakeLayerID.GREEN_FRONT_ICING_BOTTOM:
                        slot_id = CakeSlotID.GREEN_FRONT_ICING
                    case CakeLayerID.GREEN_FRONT_CREAM_BOTTOM:
                        slot_id = CakeSlotID.GREEN_FRONT_CREAM
                    case CakeLayerID.GREEN_FRONT_SPONGE_BOTTOM:
                        slot_id = CakeSlotID.GREEN_FRONT_SPONGE
                    case CakeLayerID.GREEN_BACK_SPONGE_BOTTOM:
                        slot_id = CakeSlotID.GREEN_BACK_SPONGE
                    case CakeLayerID.GREEN_BACK_CREAM_BOTTOM:
                        slot_id = CakeSlotID.GREEN_BACK_CREAM
                    case CakeLayerID.GREEN_BACK_ICING_BOTTOM:
                        slot_id = CakeSlotID.GREEN_BACK_ICING
                    case CakeLayerID.BLUE_FRONT_ICING_BOTTOM:
                        slot_id = CakeSlotID.BLUE_FRONT_ICING
                    case CakeLayerID.BLUE_FRONT_CREAM_BOTTOM:
                        slot_id = CakeSlotID.BLUE_FRONT_CREAM
                    case CakeLayerID.BLUE_FRONT_SPONGE_BOTTOM:
                        slot_id = CakeSlotID.BLUE_FRONT_SPONGE
                    case CakeLayerID.BLUE_BACK_SPONGE_BOTTOM:
                        slot_id = CakeSlotID.BLUE_BACK_SPONGE
                    case CakeLayerID.BLUE_BACK_CREAM_BOTTOM:
                        slot_id = CakeSlotID.BLUE_BACK_CREAM
                    case CakeLayerID.BLUE_BACK_ICING_BOTTOM:
                        slot_id = CakeSlotID.BLUE_BACK_ICING
                slot = CakeSlot(slot_id, layer.x, layer.y, layer.kind, cake)
                self.cake_slots[slot_id] = slot

            cake.layers[layer.pos] = layer

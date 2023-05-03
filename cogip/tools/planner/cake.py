from cogip.models.artifacts import CakeLayer, CakeLayerKind, CakeLayerPos
from cogip.models.models import DynRoundObstacle
from .properties import Properties
from . import robot


class Cake:
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self._x = x
        self._y = y
        self.robot: robot.Robot | None = None
        self.on_table: bool = True
        self.layers: dict[CakeLayerPos, CakeLayer] = {}
        self.has_cherry: bool = False
        self.obstacle = DynRoundObstacle(x=x, y=y, radius=80)

    def update_obstacle_properties(self, properties: Properties):
        self.bb_radius = self.obstacle.radius + properties.robot_width / 2
        self.nb_vertices = properties.obstacle_bb_vertices
        self.obstacle.create_bounding_box(self.bb_radius, 6)

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, new_x: float):
        self._x = new_x
        self.obstacle.x = new_x
        self.obstacle.create_bounding_box(self.bb_radius, self.nb_vertices)

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, new_y: float):
        self._y = new_y
        self.obstacle.y = new_y
        self.obstacle.create_bounding_box(self.bb_radius, self.nb_vertices)


class CakeSlot:
    def __init__(self, x: float, y: float, kind: CakeLayerKind, cake: Cake | None = None):
        self.x = x
        self.y = y
        self.kind: CakeLayerKind = kind
        self.cake: Cake | None = cake

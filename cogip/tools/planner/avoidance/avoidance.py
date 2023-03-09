from enum import IntEnum

from cogip import models
from .. import pose


borders = [
    models.Vertex(x=0, y=1000),
    models.Vertex(x=3000, y=1000),
    models.Vertex(x=3000, y=-1000),
    models.Vertex(x=0, y=-1000)
]

fixed_obstacles = [
    [
        models.Vertex(x=0, y=15),
        models.Vertex(x=300, y=15),
        models.Vertex(x=300, y=-15),
        models.Vertex(x=0, y=-15),
    ],
    [
        models.Vertex(x=3000 - 300, y=15),
        models.Vertex(x=3000, y=15),
        models.Vertex(x=3000, y=-15),
        models.Vertex(x=3000 - 300, y=-15),
    ],
    [
        models.Vertex(x=1500 - 150, y=-1000 + 30),
        models.Vertex(x=1500 + 150, y=-1000 + 30),
        models.Vertex(x=1500 + 150, y=-1000),
        models.Vertex(x=1500 - 150, y=-1000),
    ],
    [
        models.Vertex(x=1500 - 150, y=1000),
        models.Vertex(x=1500 + 150, y=1000),
        models.Vertex(x=1500 + 150, y=1000 - 30),
        models.Vertex(x=1500 - 150, y=1000 - 30),
    ]
]

robot_width = 330


class AvoidanceStrategy(IntEnum):
    Disabled = 0


def get_path(
        pose_current: models.Pose,
        goal: pose.Pose,
        obstacles: list[models.Vertex],
        strategy: AvoidanceStrategy = AvoidanceStrategy.Disabled) -> list[pose.Pose]:
    match strategy:
        case _:
            return [pose.Pose(**pose_current.dict()), goal.copy()]


def get_path_disabled(
        start: models.Pose,
        goal: pose.Pose) -> list[pose.Pose]:
    return [pose.Pose(**start.dict()), goal.copy()]

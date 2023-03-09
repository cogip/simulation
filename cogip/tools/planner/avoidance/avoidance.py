from enum import IntEnum

from cogip import models
from cogip.utils.singleton import Singleton
from .visibility_road_map import visibility_road_map
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
    VisibilityRoadMap = 1


def get_path(
        pose_current: models.Pose,
        goal: pose.Pose,
        obstacles: list[models.Vertex],
        strategy: AvoidanceStrategy = AvoidanceStrategy.Disabled) -> list[pose.Pose]:
    match strategy:
        case AvoidanceStrategy.VisibilityRoadMap:
            return VisibilityRoadMapWrapper().get_path(pose_current, goal, obstacles)
        case _:
            return [pose.Pose(**pose_current.dict()), goal.copy()]


class VisibilityRoadMapWrapper(metaclass=Singleton):
    def __init__(self):
        # Convert fixed obstacles
        self.fixed_obstacles: list[visibility_road_map.ObstaclePolygon] = []
        x_list, y_list = list(zip(*[(int(v.x), int(v.y)) for v in borders]))
        self.fixed_obstacles.append(visibility_road_map.ObstaclePolygon(list(x_list), list(y_list)))
        for obstacle in fixed_obstacles:
            x_list, y_list = list(zip(*[(int(v.x), int(v.y)) for v in obstacle]))
            self.fixed_obstacles.append(visibility_road_map.ObstaclePolygon(list(x_list), list(y_list)))

        self.expand_distance = robot_width / 2

    def get_path(
            self,
            start: models.Pose,
            goal: pose.Pose,
            obstacles: list[models.Vertex]) -> list[pose.Pose]:
        converted_obstacles = self.fixed_obstacles.copy()
        for obstacle in obstacles:
            if not isinstance(obstacle, models.DynRoundObstacle):
                continue
            x_list, y_list = list(zip(*[(int(v.x), int(v.y)) for v in obstacle.bb]))
            converted_obstacles.append(visibility_road_map.ObstaclePolygon(list(x_list), list(y_list)))

        # Compute path
        rx, ry = visibility_road_map.VisibilityRoadMap(self.expand_distance).planning(
            start.x, start.y,
            goal.x, goal.y, converted_obstacles)

        # Convert computed path in the planner format
        path = [pose.Pose(x=x, y=y) for x, y in zip(rx, ry)]

        if len(path) == 1:
            # No path found, or start and goal are the same pose
            return []

        if len(path) > 1:
            # Replace first and last poses with original start and goal
            # to preserve the same properties (like orientation)
            path[-1] = goal.copy()
            path[0] = pose.Pose(**start.dict())

        return path

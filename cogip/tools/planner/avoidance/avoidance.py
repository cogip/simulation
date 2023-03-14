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
        models.Vertex(x=1500 - 150, y=1000 - 30),
        models.Vertex(x=1500 + 150, y=1000 - 30),
        models.Vertex(x=1500 + 150, y=1000),
        models.Vertex(x=1500 - 150, y=1000),
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
        self.fixed_obstacles: list[visibility_road_map.ObstaclePolygon] = []
        for obstacle in fixed_obstacles:
            x_list, y_list = list(zip(*[(int(v.x), int(v.y)) for v in obstacle]))
            x_list = list(x_list)
            y_list = list(y_list)
            x_list.append(x_list[0])
            y_list.append(y_list[0])
            self.fixed_obstacles.append(visibility_road_map.ObstaclePolygon(x_list, y_list, robot_width))

        self.expand_distance = robot_width / 2

        self.visibility_road_map = visibility_road_map.VisibilityRoadMap(
            x_min=robot_width / 2,
            x_max=3000 - robot_width / 2,
            y_min=-1000 + robot_width / 2,
            y_max=1000 - robot_width / 2,
            fixed_obstacles=self.fixed_obstacles
        )

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
            x_list = list(x_list)
            y_list = list(y_list)
            x_list.append(x_list[0])
            y_list.append(y_list[0])
            converted_obstacles.append(visibility_road_map.ObstaclePolygon(
                x_list,
                y_list,
                robot_width * 2
            ))

        # Compute path
        rx, ry = self.visibility_road_map.planning(
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

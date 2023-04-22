from enum import IntEnum
from multiprocessing.managers import DictProxy

from cogip import models
from .visibility_road_map import visibility_road_map
from .. import pose

try:
    from .debug import DebugWindow
except ImportError:
    DebugWindow = bool


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


class AvoidanceStrategy(IntEnum):
    Disabled = 0
    VisibilityRoadMapQuadPid = 1
    VisibilityRoadMapLinearPoseDisabled = 2


class Avoidance:
    def __init__(self, robot_id: int, shared_properties: DictProxy):
        self.robot_id = robot_id
        self.shared_properties = shared_properties
        self.visibility_road_map = VisibilityRoadMapWrapper(robot_id, shared_properties)
        self.last_robot_width: int = -1
        self.last_expand: int = -1

    def get_path(
            self,
            pose_current: models.PathPose,
            goal: models.PathPose,
            obstacles: models.DynObstacleList,
            strategy: AvoidanceStrategy = AvoidanceStrategy.Disabled) -> list[models.PathPose]:
        robot_width = self.shared_properties["robot_width"]
        match strategy:
            case AvoidanceStrategy.VisibilityRoadMapQuadPid | AvoidanceStrategy.VisibilityRoadMapLinearPoseDisabled:
                expand = int(robot_width * self.shared_properties["obstacle_bb_margin"])
                if self.last_robot_width != robot_width or self.last_expand != expand:
                    self.visibility_road_map.set_properties(robot_width, expand)
                    self.last_robot_width = robot_width
                    self.last_expand = expand
                return self.visibility_road_map.get_path(pose_current, goal, obstacles)
            case _:
                return [models.PathPose(**pose_current.dict()), goal.copy()]


class VisibilityRoadMapWrapper:
    def __init__(self, robot_id: int, shared_properties: DictProxy):
        if DebugWindow and shared_properties["plot"]:
            self.win = DebugWindow(robot_id)
        else:
            self.win = None
        self.shared_properties = shared_properties
        self.robot_width: int = 0
        self.fixed_obstacles: list[visibility_road_map.ObstaclePolygon] = []

    def set_properties(self, robot_width: int, expand: int):
        self.robot_width = robot_width
        self.expand = expand
        self.fixed_obstacles.clear()

        for obstacle in fixed_obstacles:
            x_list, y_list = list(zip(*[(int(v.x), int(v.y)) for v in obstacle]))
            x_list = list(x_list)
            y_list = list(y_list)
            x_list.append(x_list[0])
            y_list.append(y_list[0])

            self.fixed_obstacles.append(visibility_road_map.ObstaclePolygon(x_list, y_list, expand))

        if self.win:
            self.win.fixed_obstacles = self.fixed_obstacles[:]

        self.visibility_road_map = visibility_road_map.VisibilityRoadMap(
            x_min=borders[0].x + robot_width / 2,
            x_max=borders[2].x - robot_width / 2,
            y_min=borders[2].y + robot_width / 2,
            y_max=borders[0].y - robot_width / 2,
            fixed_obstacles=self.fixed_obstacles,
            win=self.win
        )

    def get_path(
            self,
            start: models.PathPose,
            goal: models.PathPose,
            obstacles: models.DynObstacleList) -> list[models.PathPose]:
        if self.win:
            self.win.reset()
            self.win.point_start = start
            self.win.point_goal = goal.pose

        converted_obstacles = []

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
                self.expand
            ))
        if self.win:
            self.win.dyn_obstacles.extend(converted_obstacles)
            self.win.update()

        # Compute path
        rx, ry = self.visibility_road_map.planning(
            start.x, start.y,
            goal.x, goal.y,
            converted_obstacles,
            self.shared_properties["max_distance"])

        if self.win:
            self.win.path = [(x, y) for x, y in zip(rx, ry)]
            self.win.update()

        # Convert computed path in the planner format
        path = [models.PathPose(x=x, y=y) for x, y in zip(rx, ry)]

        if len(path) == 1:
            # No path found, or start and goal are the same pose
            return []

        if len(path) > 1:
            # Replace first and last poses with original start and goal
            # to preserve the same properties (like orientation)
            path[-1] = goal.copy()
            path[0] = models.PathPose(**start.dict())

        return path

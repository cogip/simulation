import math
from multiprocessing import Queue
from multiprocessing.managers import DictProxy
import time

from cogip import models
from cogip.tools.copilot.controller import ControllerEnum
from .. import logger
from ..table import Table
from ..strategy import Strategy
from .avoidance import Avoidance, AvoidanceStrategy


def create_dyn_obstacle(
        center: models.Vertex,
        shared_properties: DictProxy,
        radius: float | None = None,
        bb_radius: float | None = None) -> models.DynRoundObstacle:
    """
    Create a dynamic obstacle.

    Arguments:
        center: center of the obstacle
        radius: radius of the obstacle, use the value from global properties if not specified
        bb_radius: radius of the bounding box
    """
    if radius is None:
        radius = shared_properties["obstacle_radius"]

    if bb_radius is None:
        bb_radius = radius + shared_properties["robot_width"] / 2

    bb = [
        models.Vertex(
            x=center.x + bb_radius * math.cos(
                (tmp := (i * 2 * math.pi) / shared_properties["obstacle_bb_vertices"])
            ),
            y=center.y + bb_radius * math.sin(tmp),
        )
        for i in reversed(range(shared_properties["obstacle_bb_vertices"]))
    ]

    return models.DynRoundObstacle(
        x=center.x,
        y=center.y,
        radius=radius,
        bb=bb
    )


def avoidance_process(
        robot_id: int,
        strategy: Strategy,
        avoidance_strategy: AvoidanceStrategy,
        table: Table,
        shared_properties: DictProxy,
        shared_exiting: DictProxy,
        shared_poses_current: DictProxy,
        shared_poses_order: DictProxy,
        shared_obstacles: DictProxy,
        shared_last_avoidance_pose_currents: DictProxy,
        queue_sio: Queue):

    avoidance = Avoidance(robot_id, table, shared_properties)
    avoidance_path: list[models.PathPose] = []
    last_emitted_pose_order: models.PathPose | None = None
    start = time.time() - shared_properties["path_refresh_interval"] + 0.01

    while not shared_exiting[robot_id]:
        queue_sio.put(("path", (robot_id, [pose.pose.dict(exclude_defaults=True) for pose in avoidance_path])))
        path_refresh_interval = shared_properties["path_refresh_interval"]

        now = time.time()
        duration = now - start
        if duration > path_refresh_interval:
            logger.warning(f"Avoidance Process {robot_id}: {duration:0.3f}ms > {path_refresh_interval:0.3f}ms")
        else:
            wait = path_refresh_interval - duration
            time.sleep(wait)
        start = time.time()

        if strategy in [Strategy.LinearSpeedTest, Strategy.AngularSpeedTest]:
            avoidance_path = []
            continue

        pose_current = shared_poses_current.get(robot_id)
        pose_order = shared_poses_order.get(robot_id)
        if not pose_current or not pose_order:
            avoidance_path = []
            continue
        pose_current = models.PathPose.parse_obj(pose_current)
        pose_order = models.PathPose.parse_obj(pose_order)

        if pose_order.pose == pose_current:
            avoidance_path = []
            continue

        # Check if robot has moved enough since the last avoidance path was computed
        if robot_id in shared_last_avoidance_pose_currents and \
            shared_last_avoidance_pose_currents[robot_id] != (pose_current.x, pose_current.y) and \
            (dist := math.dist(
                (pose_current.x, pose_current.y),
                (shared_last_avoidance_pose_currents[robot_id][0], shared_last_avoidance_pose_currents[robot_id][1]))
             ) < 20:
            logger.debug(f"Robot {robot_id}: Skip avoidance path update (current pose too close: {dist:0.2f})")
            avoidance_path = []
            continue

        shared_last_avoidance_pose_currents[robot_id] = (pose_current.x, pose_current.y)

        # Create an obstacle for other robots
        other_robot_obstacles = [
            create_dyn_obstacle(models.PathPose.parse_obj(p), shared_properties, radius=shared_properties["robot_width"] / 2)
            for rid, p in shared_poses_current.items()
            if rid != robot_id
        ]

        dyn_obstacles = []

        if robot_id in shared_obstacles:
            dyn_obstacles = [
                models.DynRoundObstacle.parse_obj(obstacle)
                for obstacle in shared_obstacles[robot_id]
            ]

        # Exclude dynamic obstacles detected near robot positions
        filtered_dyn_obstacles: models.DynObstacleList = []
        min_dist: float = 100.0  # minimum distance to other robots to exclude obstacles
        for obstacle in dyn_obstacles:
            for p in shared_poses_current.values():
                if math.dist((obstacle.x, obstacle.y), (p["x"], p["y"])) < min_dist:
                    continue
            filtered_dyn_obstacles.append(obstacle)

        path = avoidance.get_path(
            pose_current,
            pose_order,
            filtered_dyn_obstacles + other_robot_obstacles,
            avoidance_strategy
        )

        if len(path) == 0:
            logger.debug(f"Robot {robot_id}: No path found")
            if robot_id in shared_last_avoidance_pose_currents:
                del shared_last_avoidance_pose_currents[robot_id]
            avoidance_path = []
            continue

        for p in path:
            p.allow_reverse = pose_order.allow_reverse

        if len(path) == 1:
            # Only one pose in path means the pose order is reached and robot is waiting next order,
            # so do nothing.
            avoidance_path = []
            continue

        if len(path) == 2:
            # Final pose
            new_controller = ControllerEnum.QUADPID
        else:
            # Intermediate pose
            match avoidance_strategy:
                case AvoidanceStrategy.Disabled | AvoidanceStrategy.VisibilityRoadMapQuadPid:
                    new_controller = ControllerEnum.QUADPID
                case AvoidanceStrategy.VisibilityRoadMapLinearPoseDisabled:
                    new_controller = ControllerEnum.LINEAR_POSE_DISABLED

            if len(avoidance_path) >= 2:
                dist = math.dist(
                    (path[1].x, path[1].y),
                    (avoidance_path[1].x, avoidance_path[1].y)
                )
                if dist < 20:
                    logger.debug(f"Robot {robot_id}: Skip path update (new intermediate pose too close: {dist:0.2f})")
                    continue
                logger.debug(f"Robot {robot_id}: Update avoidance path")

            next_delta_x = path[2].x - path[1].x
            next_delta_y = path[2].y - path[1].y

            path[1].O = math.degrees(math.atan2(next_delta_y, next_delta_x))  # noqa
            path[1].allow_reverse = True

        avoidance_path = path[:]
        new_pose_order = path[1].copy()

        if last_emitted_pose_order != new_pose_order:

            last_emitted_pose_order = new_pose_order.copy()

            if robot_id in shared_properties["controllers"] \
               and shared_properties["controllers"][robot_id] != new_controller:
                queue_sio.put(("set_controller", (robot_id, new_controller.value)))

            queue_sio.put(("pose_order", (robot_id, new_pose_order.dict(exclude_defaults=True))))

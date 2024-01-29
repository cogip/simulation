import math
import time
from multiprocessing import Queue
from multiprocessing.managers import DictProxy, Namespace

from cogip import models
from cogip.tools.copilot.controller import ControllerEnum
from .. import logger
from ..strategy import Strategy
from ..table import Table
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

    obstacle = models.DynRoundObstacle(
        x=center.x,
        y=center.y,
        radius=radius
    )
    obstacle.create_bounding_box(bb_radius, shared_properties["obstacle_bb_vertices"])

    return obstacle


def avoidance_process(
        robot: Namespace,
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
    robot_id = robot.robot_id
    logger.info(f"Avoidance {robot_id}: process started")
    avoidance = Avoidance(robot_id, table, shared_properties)
    avoidance_path: list[models.PathPose] = []
    last_emitted_pose_order: models.PathPose | None = None
    start = time.time() - shared_properties["path_refresh_interval"] + 0.01
    min_dist: float = 100.0  # minimum distance to other robots to exclude obstacles

    while not shared_exiting[robot_id]:
        queue_sio.put(("avoidance_path", [pose.pose.model_dump(exclude_defaults=True) for pose in avoidance_path]))
        path_refresh_interval = shared_properties["path_refresh_interval"]

        now = time.time()
        duration = now - start
        if duration > path_refresh_interval:
            logger.warning(f"Avoidance Process {robot_id}: {duration:0.3f}ms > {path_refresh_interval:0.3f}ms")
        else:
            wait = path_refresh_interval - duration
            time.sleep(wait)
        start = time.time()

        avoidance_path = []

        pose_current = shared_poses_current.get(robot_id)
        pose_order = shared_poses_order.get(robot_id)
        if not pose_current or not pose_order:
            logger.debug(f"Avoidance {robot_id}: Skip path update (no pose current or no pose order)")
            continue
        pose_current = models.PathPose.model_validate(pose_current)
        pose_order = models.PathPose.model_validate(pose_order)

        if strategy in [Strategy.LinearSpeedTest, Strategy.AngularSpeedTest]:
            logger.debug(f"Avoidance {robot_id}: Skip path update (speed test)")
            continue

        if pose_order.pose == pose_current:
            logger.debug(f"Avoidance {robot_id}: Skip path update (pose_current = order_order)")
            continue

        # Check if robot has moved enough since the last avoidance path was computed
        if robot_id in shared_last_avoidance_pose_currents and \
            shared_last_avoidance_pose_currents[robot_id] != (pose_current.x, pose_current.y) and \
            (dist := math.dist(
                (pose_current.x, pose_current.y),
                (shared_last_avoidance_pose_currents[robot_id][0], shared_last_avoidance_pose_currents[robot_id][1]))
             ) < 20:
            logger.debug(f"Avoidance {robot_id}: Skip path update (current pose too close: {dist:0.2f})")
            continue

        # Create an obstacle for other robots
        other_robot_obstacles = [
            create_dyn_obstacle(
                models.PathPose.model_validate(p),
                shared_properties,
                radius=shared_properties["robot_width"] / 1.5
            )
            for rid, p in shared_poses_current.items()
            if rid != robot_id
        ]

        # Create dynamic obstacles
        dyn_obstacles = [
            models.DynRoundObstacle.model_validate(obstacle)
            for obstacle in shared_obstacles.get(robot_id, [])
        ]

        # Filter dynamic obstacles by excluding obstacles detected near robot positions
        filtered_dyn_obstacles: models.DynObstacleList = []
        for obstacle in dyn_obstacles:
            for p in shared_poses_current.values():
                if math.dist((obstacle.x, obstacle.y), (p["x"], p["y"])) < min_dist:
                    continue
            filtered_dyn_obstacles.append(obstacle)

        # Gather all obstacles
        all_obstacles = filtered_dyn_obstacles + other_robot_obstacles

        if any([obstacle.contains(pose_current.pose) for obstacle in all_obstacles]):
            logger.debug(f"Avoidance {robot_id}: pose current in obstacle")
            path = []
        elif any([obstacle.contains(pose_order.pose) for obstacle in all_obstacles]):
            logger.debug(f"Avoidance {robot_id}: pose order in obstacle")
            path = []
        else:
            shared_last_avoidance_pose_currents[robot_id] = (pose_current.x, pose_current.y)

            path = avoidance.get_path(
                pose_current,
                pose_order,
                all_obstacles,
                avoidance_strategy
            )

        if len(path) == 0:
            logger.debug(f"Avoidance {robot_id}: No path found")
            if robot_id in shared_last_avoidance_pose_currents:
                del shared_last_avoidance_pose_currents[robot_id]
            queue_sio.put(("blocked", None))
            continue

        for p in path:
            p.allow_reverse = pose_order.allow_reverse

        if len(path) == 1:
            # Only one pose in path means the pose order is reached and robot is waiting next order,
            # so do nothing.
            logger.debug(f"Avoidance {robot_id}: len(path) == 1")
            continue

        if len(path) == 2:
            # Final pose
            new_controller = ControllerEnum.QUADPID
            if path[1].O is None:
                path[1].O = path[0].O  # noqa
        else:
            # Intermediate pose
            match avoidance_strategy:
                case AvoidanceStrategy.Disabled | AvoidanceStrategy.VisibilityRoadMapQuadPid:
                    new_controller = ControllerEnum.QUADPID
                case AvoidanceStrategy.VisibilityRoadMapLinearPoseDisabled:
                    new_controller = ControllerEnum.LINEAR_POSE_DISABLED

            if len(path) > 2 and last_emitted_pose_order:
                dist = math.dist(
                    (last_emitted_pose_order.x, last_emitted_pose_order.y),
                    (path[1].x, path[1].y)
                )
                if dist < 20:
                    logger.debug(f"Avoidance {robot_id}: Skip path update (new intermediate pose too close: {dist:0.2f})")
                    continue

            next_delta_x = path[2].x - path[1].x
            next_delta_y = path[2].y - path[1].y

            path[1].O = math.degrees(math.atan2(next_delta_y, next_delta_x))  # noqa
            path[1].allow_reverse = True

        avoidance_path = path[1:]
        new_pose_order = path[1]

        if last_emitted_pose_order == new_pose_order:
            logger.debug(f"Avoidance {robot_id}: ignore path update (last_emitted_pose_order == new_pose_order)")
            continue

        last_emitted_pose_order = new_pose_order.model_copy()

        if robot.controller != new_controller:
            queue_sio.put(("set_controller", new_controller.value))

        logger.debug(f"Avoidance {robot_id}: Update path")
        queue_sio.put(("pose_order", new_pose_order.model_dump(exclude_defaults=True)))
        queue_sio.put(("path", [pose.pose.model_dump(exclude_defaults=True) for pose in avoidance_path]))

    logger.info(f"Avoidance {robot_id}: process exited")

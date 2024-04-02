import math
import time
from multiprocessing import Queue
from multiprocessing.managers import DictProxy

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
    bb_radius: float | None = None,
) -> models.DynRoundObstacle:
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
        radius=radius,
    )
    obstacle.create_bounding_box(bb_radius, shared_properties["obstacle_bb_vertices"])

    return obstacle


def avoidance_process(
    strategy: Strategy,
    avoidance_strategy: AvoidanceStrategy,
    table: Table,
    shared_properties: DictProxy,
    queue_sio: Queue,
):
    logger.info("Avoidance: process started")
    avoidance = Avoidance(table, shared_properties)
    avoidance_path: list[models.PathPose] = []
    last_emitted_pose_order: models.PathPose | None = None
    start = time.time() - shared_properties["path_refresh_interval"] + 0.01

    while not shared_properties["exiting"]:
        queue_sio.put(("avoidance_path", [pose.pose.model_dump(exclude_defaults=True) for pose in avoidance_path]))
        path_refresh_interval = shared_properties["path_refresh_interval"]

        now = time.time()
        duration = now - start
        if duration > path_refresh_interval:
            logger.warning(f"Avoidance: {duration:0.3f}ms > {path_refresh_interval:0.3f}ms")
        else:
            wait = path_refresh_interval - duration
            time.sleep(wait)
        start = time.time()

        avoidance_path = []

        pose_current = shared_properties["pose_current"]
        pose_order = shared_properties["pose_order"]
        if not pose_current:
            logger.debug("Avoidance: Skip path update (no pose current)")
            continue
        if not pose_order:
            logger.debug("Avoidance: Skip path update (no pose order)")
            continue
        pose_current = models.PathPose.model_validate(pose_current)
        pose_order = models.PathPose.model_validate(pose_order)

        if strategy in [Strategy.LinearSpeedTest, Strategy.AngularSpeedTest]:
            logger.debug("Avoidance: Skip path update (speed test)")
            continue

        if pose_order.pose == pose_current:
            logger.debug("Avoidance: Skip path update (pose_current = order_order)")
            continue

        # Check if robot has moved enough since the last avoidance path was computed
        if (
            (last_avoidance_pose_current := shared_properties["last_avoidance_pose_current"])
            and last_avoidance_pose_current != (pose_current.x, pose_current.y)
            and (
                dist := math.dist(
                    (pose_current.x, pose_current.y),
                    (
                        last_avoidance_pose_current[0],
                        last_avoidance_pose_current[1],
                    ),
                )
            )
            < 20
        ):
            logger.debug(f"Avoidance: Skip path update (current pose too close: {dist:0.2f})")
            continue

        # Create dynamic obstacles
        dyn_obstacles = [
            models.DynRoundObstacle.model_validate(obstacle) for obstacle in shared_properties["obstacles"]
        ]

        if any([obstacle.contains(pose_current.pose) for obstacle in dyn_obstacles]):
            logger.debug("Avoidance: pose current in obstacle")
            path = []
        elif any([obstacle.contains(pose_order.pose) for obstacle in dyn_obstacles]):
            logger.debug("Avoidance: pose order in obstacle")
            path = []
        else:
            shared_properties["last_avoidance_pose_current"] = (pose_current.x, pose_current.y)

            if pose_current.x == pose_order.x and pose_current.y == pose_order.y and pose_current.O != pose_order.O:
                # If the pose order is just a rotation from the pose current, the avoidance will not find any path,
                # so set the path manually
                logger.debug("Avoidance: rotation only")
                path = [pose_current, pose_order]
            else:
                path = avoidance.get_path(pose_current, pose_order, dyn_obstacles, avoidance_strategy)

        if len(path) == 0:
            logger.debug("Avoidance: No path found")
            shared_properties["last_avoidance_pose_current"] = None
            queue_sio.put(("blocked", None))
            continue

        for p in path:
            p.allow_reverse = pose_order.allow_reverse

        if len(path) == 1:
            # Only one pose in path means the pose order is reached and robot is waiting next order,
            # so do nothing.
            logger.debug("Avoidance: len(path) == 1")
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
                dist = math.dist((last_emitted_pose_order.x, last_emitted_pose_order.y), (path[1].x, path[1].y))
                if dist < 20:
                    logger.debug(f"Avoidance: Skip path update (new intermediate pose too close: {dist:0.2f})")
                    continue

            next_delta_x = path[2].x - path[1].x
            next_delta_y = path[2].y - path[1].y

            path[1].O = math.degrees(math.atan2(next_delta_y, next_delta_x))  # noqa
            path[1].allow_reverse = True

        avoidance_path = path[1:]
        new_pose_order = path[1]

        if last_emitted_pose_order == new_pose_order:
            logger.debug("Avoidance: ignore path update (last_emitted_pose_order == new_pose_order)")
            continue

        last_emitted_pose_order = new_pose_order.model_copy()

        if shared_properties["controller"] != new_controller:
            queue_sio.put(("set_controller", new_controller.value))

        logger.debug("Avoidance: Update path")
        queue_sio.put(("pose_order", new_pose_order.model_dump(exclude_defaults=True)))
        queue_sio.put(("path", [pose.pose.model_dump(exclude_defaults=True) for pose in avoidance_path]))

    logger.info("Avoidance: process exited")

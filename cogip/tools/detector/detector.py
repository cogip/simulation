import math
import threading
import time
from typing import List, Optional, Tuple

import socketio

from cogip import models
from cogip.utils import ThreadLoop
from . import logger
from .sio_events import SioEvents


class Detector:
    """
    Main detector class.

    Read Lidar data from the Lidar in monitoring mode (TODO)
    or fake data provided by `Monitor` in emulation Mode.

    Build obstacles and send the list to the server.
    """
    NB_ANGLES: int = 360
    NB_ANGLES_WITHOUT_OBSTACLE_TO_IGNORE: int = 3

    def __init__(
            self,
            server_url: str,
            uart_port: Optional[str],
            uart_speed: int,
            min_distance: int,
            max_distance: int,
            min_intensity: int,
            obstacle_radius: int,
            obstacle_bb_margin: int,
            obstacle_bb_vertices: int,
            beacon_radius: int,
            refresh_interval: float):
        """
        Class constructor.

        Arguments:
            server_url: server URL
            uart_port: Serial port connected to the Lidar
            uart_speed: Baud rate
            server_url: Server URL
            min_distance: Minimum distance to detect an obstacle
            max_distance: Maximum distance to detect an obstacle
            min_intensity: Minimum intensity required to validate a Lidar distance
            obstacle_radius: Radius of a dynamic obstacle
            obstacle_bb_margin: Obstacle bounding box margin in percent of the radius
            obstacle_bb_vertices: Number of obstacle bounding box vertices
            beacon_radius: Radius of the opponent beacon support (a cylinder of 70mm diameter to a cube of 100mm width)
            refresh_interval: Interval between each update of the obstacle list (in seconds)
        """
        self._server_url = server_url
        self._uart_port = uart_port
        self._uart_speed = uart_speed
        self._min_distance = min_distance
        self._max_distance = max_distance
        self._min_intensity = min_intensity
        self._obstacle_radius = obstacle_radius
        self._obstacle_bb_margin = obstacle_bb_margin
        self._obstacle_bb_vertices = obstacle_bb_vertices
        self._beacon_radius = beacon_radius
        self._retry_connection = True
        self._lidar_data: List[int] = list()
        self._lidar_data_lock = threading.Lock()
        self._robot_pose = models.Pose()
        self._robot_pose_lock = threading.Lock()

        self._obstacles_updater_loop = ThreadLoop(
            "Obstacles updater loop",
            refresh_interval,
            self.process_lidar_data,
            logger=True
        )

        self._sio = socketio.Client(logger=False)
        self._sio.register_namespace(SioEvents(self))

    def connect(self):
        """
        Connect to SocketIO server.
        """
        self.retry_connection = True
        threading.Thread(target=self.try_connect).start()

    def start_obstacles_updater(self) -> None:
        """
        Start the thread updating obstacles list.
        """
        self._obstacles_updater_loop.start()

    def stop_obstacles_updater(self) -> None:
        """
        Stop the thread updating obstacles list.
        """
        self._obstacles_updater_loop.stop()

    def try_connect(self):
        """
        Poll to wait for the first cogip-server connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while(self.retry_connection):
            try:
                self._sio.connect(
                    self._server_url,
                    socketio_path="sio/socket.io",
                    namespaces=["/detector"],
                    auth={
                        "mode": "detection" if self._uart_port else "emulation"
                    }
                )
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    @property
    def try_reconnection(self) -> bool:
        """
        Return true if Detector should continue to try to connect to cogip-server,
        false otherwise.
        """
        return self._retry_connection

    @try_reconnection.setter
    def try_reconnection(self, new_value: bool) -> None:
        self._retry_connection = new_value

    @property
    def robot_pose(self) -> models.Pose:
        """
        Last position of the robot.
        """
        return self._robot_pose

    @robot_pose.setter
    def robot_pose(self, new_pose: models.Pose) -> None:
        with self._robot_pose_lock:
            self._robot_pose = new_pose

    def normalize_distance(self, distance: int, intensity: int) -> int:
        """
        Normalize a Lidar distance (for one angle) based on maximum and
        minimum authorized distances, and minimum intensity of the Lidar signal.
        """
        if self._max_distance == 0:
            return distance

        if intensity < self._min_intensity or distance == 0 or distance > self._max_distance:
            return self._max_distance

        return distance

    def update_lidar_data(self, lidar_data: List[Tuple[int, int]]):
        """
        Receive Lidar data and normalize them.
        """
        with self._lidar_data_lock:
            self._lidar_data = [self.normalize_distance(d + self._beacon_radius, i) for d, i in lidar_data]

    def filter_distances(self) -> List[int]:
        """
        Find consecutive obstacles and keep the nearest obstacle at the middle.
        """
        filtered_distances = [self._max_distance] * self.NB_ANGLES

        # Find an angle without obstacle
        angles_without_obstacles = [i for i, d in enumerate(self._lidar_data) if d >= self._max_distance]

        # Exit if no obstacle detected
        if len(angles_without_obstacles) == 0:
            return filtered_distances

        start = angles_without_obstacles[0]

        # Iterate over all angles, starting by the first angle without obstacle
        first = start
        while first < start + self.NB_ANGLES:
            dist_min = self._lidar_data[first % self.NB_ANGLES]

            # Find the next angle with obstacle
            if dist_min >= self._max_distance:
                first += 1
                continue

            # An angle (first) with obstacle is found, iterate until the next obstacle without obstacle
            for last in range(first + 1, start + self.NB_ANGLES + 1):
                dist_current = self._lidar_data[last % self.NB_ANGLES]

                # Keep the nearest distance of consecutive obstacles
                if dist_current < self._max_distance or self._lidar_data[(last + 1) % self.NB_ANGLES] < self._max_distance:
                    dist_min = dist_current if dist_current < dist_min else dist_min
                    continue

                # Do not exit the loop only if NB_ANGLES_WITHOUT_OBSACLE_TO_IGNORE consecutive
                # angles have no obstacle.
                continue_loop = False
                for next in range(last + 1, last + self.NB_ANGLES_WITHOUT_OBSTACLE_TO_IGNORE):
                    if self._lidar_data[next % self.NB_ANGLES] < self._max_distance:
                        continue_loop = True
                        break

                if continue_loop:
                    continue

                # Only keep one angle at the middle of the consecutive angles with obstacles
                # Set its distance to the minimun distance of the range
                last = last - 1
                middle = first + int((last - first) / 2 + 0.5)
                filtered_distances[middle % self.NB_ANGLES] = dist_min
                first = last + 1
                break
            first += 1

        return filtered_distances

    def generate_obstacles(self, robot_pose: models.Pose, distances: List[int]):
        """
        Update obstacles list from lidar data.
        """
        obstacles = []

        for angle, distance in enumerate(distances):
            if distance < self._min_distance or distance >= self._max_distance:
                continue

            angle = (self.NB_ANGLES - angle) % self.NB_ANGLES

            # Compute obstacle position
            obstacle_angle = math.radians((int(robot_pose.O) + angle) % self.NB_ANGLES)
            x = robot_pose.x + distance * math.cos(obstacle_angle)
            y = robot_pose.y + distance * math.sin(obstacle_angle)

            # Compute bounding box
            bb_radius = self._obstacle_radius * (1 + self._obstacle_bb_margin)
            bb = [
                models.Vertex(
                    x=x + bb_radius * math.cos((tmp := (i * 2 * math.pi) / self._obstacle_bb_vertices)),
                    y=y + bb_radius * math.sin(tmp),
                )
                for i in range(self._obstacle_bb_vertices)
            ]

            obstacles.append(models.DynRoundObstacle(
                x=x,
                y=y,
                radius=self._obstacle_radius,
                bb=bb
            ))

        return obstacles

    def process_lidar_data(self):
        """
        Function executed in a thread loop to update and send dynmic obstacles.
        """
        with self._lidar_data_lock:
            filtered_distances = self.filter_distances()
        with self._robot_pose_lock:
            robot_pose = self.robot_pose.copy()

        obstacles = self.generate_obstacles(robot_pose, filtered_distances)
        logger.debug(f"Generated obstacles: {obstacles}")
        if self._sio.connected:
            self._sio.emit("obstacles", [o.dict() for o in obstacles], namespace="/detector")

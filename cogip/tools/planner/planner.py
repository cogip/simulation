import threading
import time
from typing import Dict

import socketio

from cogip import models
from cogip.utils import ThreadLoop
from .sio_events import SioEvents
from .path import available_paths, Path
from . import logger


class Planner:
    """
    Main planner class.
    """

    def __init__(
            self,
            server_url: str):
        """
        Class constructor.

        Arguments:
            server_url: Server URL
        """
        self._server_url = server_url
        self._retry_connection = True
        self._paths: Dict[int, Path] = dict()
        self._robot_pose: Dict[int, models.Pose()] = dict()
        self._pose_reached: Dict[int, bool] = dict()
        self._obstacles: Dict[int, models.DynObstacleList] = dict()
        self._sio = socketio.Client(logger=False)
        self._sio_ns = SioEvents(self)
        self._sio.register_namespace(self._sio_ns)

        self._obstacles_sender_loop = ThreadLoop(
            "Obstacles sender loop",
            0.5,
            self.send_obstacles,
            logger=True
        )

    def connect(self):
        """
        Connect to SocketIO server.
        """
        self.retry_connection = True
        threading.Thread(target=self.try_connect).start()

    def try_connect(self):
        """
        Poll to wait for the first connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while(self.retry_connection):
            try:
                self._sio.connect(
                    self._server_url,
                    socketio_path="sio/socket.io",
                    namespaces=["/planner"]
                )
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    @property
    def try_reconnection(self) -> bool:
        """
        Return true if Planner should continue to try to connect to the server,
        false otherwise.
        """
        return self._retry_connection

    @try_reconnection.setter
    def try_reconnection(self, new_value: bool) -> None:
        self._retry_connection = new_value

    def start(self) -> None:
        """
        Start sending obstacles list.
        """
        self._obstacles_sender_loop.start()

    def stop(self) -> None:
        """
        Stop sending obstacles list.
        """
        self._obstacles_sender_loop.stop()

    def add_robot(self, robot_id: int) -> None:
        """
        Add a new robot.
        """
        if self._paths.get(robot_id) is None:
            self._paths[robot_id] = available_paths.pop(0)
        self._robot_pose[robot_id] = models.Pose()
        self._pose_reached[robot_id] = True
        self._obstacles[robot_id] = []

    def del_robot(self, robot_id: int) -> None:
        """
        Remove a robot.
        """
        del self._pose_reached[robot_id]
        del self._robot_pose[robot_id]
        del self._obstacles[robot_id]
        path = self._paths.pop(robot_id)
        path.reset()
        available_paths.append(path)

    def set_pose_current(self, robot_id: int, pose: models.Pose) -> None:
        """
        Pose reached action.
        """
        self._robot_pose[robot_id] = models.Pose.parse_obj(pose)

    def set_pose_reached(self, robot_id: int) -> None:
        """
        Pose reached action.
        """
        self._pose_reached[robot_id] = True
        if self._paths[robot_id].playing:
            self._pose_reached[robot_id] = False
            self._sio_ns.emit("pose_order", (robot_id, self._paths[robot_id].incr().dict()))

    def set_obstacles(self, robot_id: int, obstacles: models.DynObstacleList) -> None:
        self._obstacles[robot_id] = obstacles

    def send_obstacles(self) -> None:
        all_obstacles = sum(self._obstacles.values(), start=[])
        self._sio_ns.emit("obstacles", [o.dict() for o in all_obstacles])

    def reset(self) -> None:
        list(map(self.cmd_reset, self._paths.keys()))

    def command(self, cmd: str) -> None:
        """
        Execute command.
        """
        cmd_func = getattr(self, f"cmd_{cmd}", None)
        if cmd_func:
            list(map(cmd_func, self._paths.keys()))
        else:
            logger.warning(f"Unknown command: {cmd}")

    def cmd_play(self, robot_id: int) -> None:
        path = self._paths[robot_id]
        path.play()
        if self._pose_reached[robot_id]:
            self._pose_reached[robot_id] = False
            self._sio_ns.emit("pose_order", (robot_id, path.incr().dict()))

    def cmd_stop(self, robot_id: int) -> None:
        path = self._paths[robot_id]
        path.stop()

    def cmd_next(self, robot_id: int) -> None:
        path = self._paths[robot_id]
        if self._pose_reached[robot_id]:
            self._pose_reached[robot_id] = False
            self._sio_ns.emit("pose_order", (robot_id, path.incr().dict()))

    def cmd_prev(self, robot_id: int) -> None:
        path = self._paths[robot_id]
        if self._pose_reached[robot_id]:
            self._pose_reached[robot_id] = False
            self._sio.emit("pose_order", (robot_id, path.decr().dict()))

    def cmd_reset(self, robot_id: int) -> None:
        """
        Reset path.
        """
        path = self._paths[robot_id]
        path.reset()
        self._pose_reached[robot_id] = True
        self._sio_ns.emit("pose_start", (robot_id, path.pose().dict()))

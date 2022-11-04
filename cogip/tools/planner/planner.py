import threading
import time

import socketio

from cogip import models
from .sio_events import SioEvents


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
        self._robot_pose = models.Pose()
        self._robot_pose_lock = threading.Lock()

        self._sio = socketio.Client(logger=False)
        self._sio.register_namespace(SioEvents(self))

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

from typing import Any, Dict, List

import socketio

from cogip import models
from . import detector, logger


class SioEvents(socketio.ClientNamespace):
    """
    Handle all SocketIO events received by Detector.
    """

    def __init__(self, detector: "detector.Detector"):
        super().__init__()
        self._detector = detector

    def on_connect(self):
        """
        On connection to Copilot, start obstacles updater thread.
        """
        logger.info("Connected to Copilot")
        self._detector.start_obstacles_updater()

    def on_disconnect(self) -> None:
        """
        On disconnection from Copilot, stop obstacles updater thread.
        """
        logger.info("Disconnected from Copilot")
        self._detector.stop_obstacles_updater()

    def on_connect_error(self, data: Dict[str, Any]) -> None:
        """
        On connection error, check if a Detector is already connected and exit,
        or retry connection.
        """
        logger.error(f"Connect to Copilot error: {data = }")
        if (
                data and
                isinstance(data, dict) and
                (message := data.get("message")) and
                message == "A detector is already connected"
           ):
            logger.error(message)
            self._detector.retry_connection = False
            return

    def on_pose(self, data: Dict[str, Any]) -> None:
        """
        Callback on robot pose message.
        """
        self._detector.robot_pose = models.Pose.parse_obj(data)

    def on_lidar_data(self, data: List[int]) -> None:
        """
        Callback on Lidar data.
        """
        logger.debug("Received lidar data from Copilot")
        self._detector.update_lidar_data([(d, 65535) for d in data])

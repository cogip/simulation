from typing import Any, Dict, List

import socketio

from cogip import models
from . import detector, logger
from .menu import menu


class SioEvents(socketio.ClientNamespace):
    """
    Handle all SocketIO events received by Detector.
    """

    def __init__(self, detector: "detector.Detector"):
        super().__init__("/detector")
        self._detector = detector

    def on_connect(self):
        """
        On connection to cogip-server, start detector threads.
        """
        logger.info("Connected to cogip-server")
        self.emit("register_menu", {"name": "detector", "menu": menu.dict()})
        self._detector.start()

    def on_disconnect(self) -> None:
        """
        On disconnection from cogip-server, stop detector threads.
        """
        logger.info("Disconnected from cogip-server")
        self._detector.stop()

    def on_connect_error(self, data: Dict[str, Any]) -> None:
        """
        On connection error, check if a Detector is already connected and exit,
        or retry connection.
        """
        logger.error(f"Connect to cogip-server error: {data = }")
        if (
                data and
                isinstance(data, dict) and
                (message := data.get("message")) and
                message == "A detector is already connected"
           ):
            logger.error(message)
            self._detector.retry_connection = False
            return

    def on_command(self, cmd: str) -> None:
        """
        Callback on command message from dashboard.
        """
        if cmd == "config":
            # Get JSON Schema
            schema = self._detector.properties.schema()
            # Add namespace in JSON Schema
            schema["namespace"] = "/detector"
            # Add current values in JSON Schema
            for prop, value in self._detector.properties.dict().items():
                schema["properties"][prop]["value"] = value
            # Send config
            self.emit("config", schema)
        else:
            logger.warning(f"Unknown command: {cmd}")

    def on_config_updated(self, config: Dict[str, Any]) -> None:
        self._detector.properties.__setattr__(name := config["name"], config["value"])
        if name == "refresh_interval":
            self._detector.update_refresh_interval()

    def on_pose_current(self, data: Dict[str, Any]) -> None:
        """
        Callback on robot pose message.
        """
        self._detector.robot_pose = models.Pose.parse_obj(data)

    def on_lidar_data(self, data: List[int]) -> None:
        """
        Callback on Lidar data.
        """
        logger.debug("Received lidar data")
        self._detector.update_lidar_data(data)

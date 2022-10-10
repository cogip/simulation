from typing import Any, Dict

import socketio

from cogip import models
from . import planner, logger
from .menu import menu
from .path import path


class SioEvents(socketio.ClientNamespace):
    """
    Handle all SocketIO events received by Planner.
    """

    def __init__(self, planner: "planner.Planner"):
        super().__init__()
        self._planner = planner
        self._pose_reached = True

    def on_connect(self):
        """
        On connection to Copilot.
        """
        logger.info("Connected to Copilot")
        self.on_reset()

    def on_disconnect(self) -> None:
        """
        On disconnection from Copilot.
        """
        logger.info("Disconnected from Copilot")

    def on_connect_error(self, data: Dict[str, Any]) -> None:
        """
        On connection error, check if a Planner is already connected and exit,
        or retry connection.
        """
        logger.error(f"Connect to Copilot error: {data = }")
        if (
                data and
                isinstance(data, dict) and
                (message := data.get("message")) and
                message == "A planner is already connected"
           ):
            logger.error(message)
            self._planner.retry_connection = False
            return

    def on_pose(self, data: Dict[str, Any]) -> None:
        """
        Callback on robot pose message.
        """
        self._planner.robot_pose = models.Pose.parse_obj(data)

    def on_reset(self) -> None:
        """
        Callback on reset message.
        """
        path.reset()
        self._pose_reached = True
        self.emit("start_pose", path.pose().dict())
        self.emit("planner_menu", menu.dict())

    def on_command(self, cmd: str) -> None:
        if cmd == "play":
            path.play()
            if self._pose_reached:
                self._pose_reached = False
                self.emit("pose_to_reach", path.incr().dict())

        elif cmd == "stop":
            path.stop()

        elif cmd == "next":
            if self._pose_reached:
                self._pose_reached = False
                self.emit("pose_to_reach", path.incr().dict())

        elif cmd == "prev":
            if self._pose_reached:
                self._pose_reached = False
                self.emit("pose_to_reach", path.decr().dict())

        elif cmd == "reset":
            self.on_reset()

    def on_pose_reached(self) -> None:
        self._pose_reached = True
        if path.playing:
            self._pose_reached = False
            self.emit("pose_to_reach", path.incr().dict())

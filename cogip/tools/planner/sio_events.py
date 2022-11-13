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
        super().__init__("/planner")
        self._planner = planner
        self._pose_reached = True

    def on_connect(self):
        """
        On connection to cogip-server.
        """
        logger.info("Connected to cogip-server")
        self.on_reset()
        self.emit("register_menu", {"name": "planner", "menu": menu.dict()})

    def on_disconnect(self) -> None:
        """
        On disconnection from cogip-server.
        """
        logger.info("Disconnected from cogip-server")

    def on_connect_error(self, data: Dict[str, Any]) -> None:
        """
        On connection error, check if a Planner is already connected and exit,
        or retry connection.
        """
        if (
                data and
                isinstance(data, dict) and
                (message := data.get("message")) and
                message == "A planner is already connected"
           ):
            logger.error(f"Connection to cogip-server failed: {message}")
            self._planner.retry_connection = False
            return
        else:
            logger.error(f"Connection to cogip-server failed: {data = }")

    def on_reset(self) -> None:
        """
        Callback on reset message.
        """
        path.reset()
        self._pose_reached = True
        self.emit("pose_start", path.pose().dict())

    def on_pose_curent(self, data: Dict[str, Any]) -> None:
        """
        Callback on pose current message.
        """
        self._planner.robot_pose = models.Pose.parse_obj(data)

    def on_pose_reached(self) -> None:
        """
        Callback on pose reached message.
        """
        self._pose_reached = True
        if path.playing:
            self._pose_reached = False
            self.emit("pose_order", path.incr().dict())

    def on_command(self, cmd: str) -> None:
        """
        Callback on command message from dashboard.
        """
        if cmd == "play":
            path.play()
            if self._pose_reached:
                self._pose_reached = False
                self.emit("pose_order", path.incr().dict())

        elif cmd == "stop":
            path.stop()

        elif cmd == "next":
            if self._pose_reached:
                self._pose_reached = False
                self.emit("pose_order", path.incr().dict())

        elif cmd == "prev":
            if self._pose_reached:
                self._pose_reached = False
                self.emit("pose_order", path.decr().dict())

        elif cmd == "reset":
            self.on_reset()

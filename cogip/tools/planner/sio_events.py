from typing import Any, Dict
from pydantic import parse_obj_as

import socketio

from cogip import models
from . import planner, logger
from .menu import menu


class SioEvents(socketio.ClientNamespace):
    """
    Handle all SocketIO events received by Planner.
    """

    def __init__(self, planner: "planner.Planner"):
        super().__init__("/planner")
        self._planner = planner

    def on_connect(self):
        """
        On connection to cogip-server.
        """
        self._planner.start()
        self._planner.reset()
        self.emit("register_menu", {"name": "planner", "menu": menu.dict()})
        logger.info("Connected to cogip-server")

    def on_disconnect(self) -> None:
        """
        On disconnection from cogip-server.
        """
        self._planner.stop()
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

    def on_add_robot(self, robot_id: int) -> None:
        """
        Add a new robot.
        """
        self._planner.add_robot(robot_id)

    def on_del_robot(self, robot_id: int) -> None:
        """
        Remove a robot.
        """
        self._planner.del_robot(robot_id)

    def on_reset(self, robot_id: int) -> None:
        """
        Callback on reset message.
        """
        self._planner.cmd_reset(robot_id)

    def on_pose_current(self, robot_id: int, pose: Dict[str, Any]) -> None:
        """
        Callback on pose current message.
        """
        self._planner.set_pose_current(robot_id, models.Pose.parse_obj(pose))

    def on_pose_reached(self, robot_id: int) -> None:
        """
        Callback on pose reached message.
        """
        self._planner.set_pose_reached(robot_id)

    def on_command(self, cmd: str) -> None:
        """
        Callback on command message from dashboard.
        """

        self._planner.command(cmd)

    def on_obstacles(self, robot_id: int, obstacles: Dict[str, Any]):
        """
        Callback on obstacles message.
        """
        self._planner.set_obstacles(
            robot_id,
            parse_obj_as(models.DynObstacleList, obstacles)
        )

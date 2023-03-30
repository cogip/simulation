from typing import Any, Dict
from pydantic import parse_obj_as

import polling2
import socketio

from cogip import models
from . import planner, logger
from .menu import menu, wizard_test_menu


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
        polling2.poll(lambda: self.client.connected is True, step=0.2, poll_forever=True)
        logger.info("Connected to cogip-server")
        self.emit("connected")
        self._planner.start()
        self.emit("register_menu", {"name": "planner", "menu": menu.dict()})
        self.emit("register_menu", {"name": "wizard", "menu": wizard_test_menu.dict()})

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
        if data \
           and isinstance(data, dict) \
           and (message := data.get("message")) \
           and message == "A planner is already connected":
            logger.error(f"Connection to cogip-server failed: {message}")
            self._planner.retry_connection = False
            return
        else:
            logger.error(f"Connection to cogip-server failed: {data = }")

    def on_add_robot(self, robot_id: int, virtual: bool) -> None:
        """
        Add a new robot.
        """
        self._planner.add_robot(robot_id, virtual)

    def on_del_robot(self, robot_id: int) -> None:
        """
        Remove a robot.
        """
        self._planner.del_robot(robot_id)

    def on_reset(self, robot_id: int) -> None:
        """
        Callback on reset message from copilot.
        """
        self._planner.add_robot(robot_id, self._planner._robots[robot_id].virtual)

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

    def on_config_updated(self, config: dict[str, Any]) -> None:
        """
        Callback on config update from dashboard.
        """
        self._planner.update_config(config)

    def on_obstacles(self, robot_id: int, obstacles: Dict[str, Any]):
        """
        Callback on obstacles message.
        """
        self._planner.set_obstacles(
            robot_id,
            parse_obj_as(list[models.Vertex], obstacles)
        )

    def on_wizard(self, message: dict[str, Any]):
        """
        Callback on wizard message.
        """
        self._planner.wizard_response(message)

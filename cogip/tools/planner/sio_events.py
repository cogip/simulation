import asyncio
from typing import Any, Dict, TYPE_CHECKING
from pydantic import TypeAdapter

import polling2
import socketio

from cogip import models
from . import context, logger
from .menu import (
    menu, wizard_test_menu,
    actuators_menu_1, actuators_menu_2,
    cherries_menu_1, cherries_menu_2,
    cameras_menu
)

if TYPE_CHECKING:
    from .planner import Planner


class SioEvents(socketio.AsyncClientNamespace):
    """
    Handle all SocketIO events received by Planner.
    """

    def __init__(self, planner: "Planner"):
        super().__init__("/planner")
        self._planner = planner
        self._game_context = context.GameContext()

    async def on_connect(self):
        """
        On connection to cogip-server.
        """
        await asyncio.to_thread(
            polling2.poll,
            lambda: self.client.connected is True,
            step=0.2,
            poll_forever=True
        )
        logger.info("Connected to cogip-server")
        await self.emit("connected")
        await self._planner.start()
        await self.emit("register_menu", {"name": "planner", "menu": menu.model_dump()})
        await self.emit("register_menu", {"name": "wizard", "menu": wizard_test_menu.model_dump()})
        await self.emit("register_menu", {"name": "actuators1", "menu": actuators_menu_1.model_dump()})
        await self.emit("register_menu", {"name": "actuators2", "menu": actuators_menu_2.model_dump()})
        await self.emit("register_menu", {"name": "cherries1", "menu": cherries_menu_1.model_dump()})
        await self.emit("register_menu", {"name": "cherries2", "menu": cherries_menu_2.model_dump()})
        await self.emit("register_menu", {"name": "cameras", "menu": cameras_menu.model_dump()})

    async def on_disconnect(self):
        """
        On disconnection from cogip-server.
        """
        await self._planner.stop()
        logger.info("Disconnected from cogip-server")

    async def on_connect_error(self, data: Dict[str, Any]):
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

    async def on_add_robot(self, robot_id: int, virtual: bool):
        """
        Add a new robot.
        """
        await self._planner.add_robot(robot_id, virtual)

    async def on_del_robot(self, robot_id: int):
        """
        Remove a robot.
        """
        await self._planner.del_robot(robot_id)

    def on_starter_changed(self, robot_id: int, pushed: bool):
        """
        Signal received from the Monitor when the starter state changes in emulation mode.
        """
        if not (robot := self._planner._robots.get(robot_id)):
            return
        if not robot.virtual:
            return
        if not (starter := robot.starter):
            return
        if not (starter := self._planner._robots[robot_id].starter):
            return
        if pushed:
            starter.pin.drive_low()
        else:
            starter.pin.drive_high()

    async def on_reset(self, robot_id: int):
        """
        Callback on reset message from copilot.
        """
        await self._planner.add_robot(robot_id, self._planner._robots[robot_id].virtual)

    async def on_pose_current(self, robot_id: int, pose: Dict[str, Any]):
        """
        Callback on pose current message.
        """
        self._planner.set_pose_current(robot_id, models.Pose.model_validate(pose))

    async def on_pose_reached(self, robot_id: int):
        """
        Callback on pose reached message.
        """
        if not (robot := self._planner._robots.get(robot_id)):
            return

        await robot.sio_receiver_queue.put(self._planner.set_pose_reached(robot))

    async def on_command(self, cmd: str):
        """
        Callback on command message from dashboard.
        """
        await self._planner.command(cmd)

    async def on_config_updated(self, config: dict[str, Any]):
        """
        Callback on config update from dashboard.
        """
        self._planner.update_config(config)

    async def on_obstacles(self, robot_id: int, obstacles: Dict[str, Any]):
        """
        Callback on obstacles message.
        """
        self._planner.set_obstacles(
            robot_id,
            TypeAdapter(list[models.Vertex]).validate_python(obstacles)
        )

    async def on_wizard(self, message: dict[str, Any]):
        """
        Callback on wizard message.
        """
        await self._planner.wizard_response(message)

    async def on_game_end(self, robot_id: int):
        """
        Callback on game end message.
        """
        await self._planner.game_end(robot_id)

    async def on_cherries(self, count: int):
        """
        Callback on cherries message.
        """
        self._game_context.nb_cherries = count

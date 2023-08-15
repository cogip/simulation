import asyncio
from typing import Any, TYPE_CHECKING

import polling2
import socketio

from . import logger
from .menu import menu

if TYPE_CHECKING:
    from .avoidance import Avoidance


class SioEvents(socketio.AsyncClientNamespace):
    """
    Handle all SocketIO events received by Avoidance.
    """

    def __init__(self, avoidance: "Avoidance"):
        super().__init__("/avoidance")
        self._avoidance = avoidance

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
        await self.emit("connected", self._avoidance.id)
        await self.emit("register_menu", {"name": "avoidance", "menu": menu.dict()})

    async def on_disconnect(self):
        """
        On disconnection from cogip-server.
        """
        logger.info("Disconnected from cogip-server")

    async def on_connect_error(self, data: dict[str, Any]):
        """
        On connection error, check if a Planner is already connected and exit,
        or retry connection.
        """
        logger.error(f"Connection to cogip-server failed: {data.get('message')}")

    async def on_config_updated(self, config: dict[str, Any]):
        """
        Callback on config update from dashboard.
        """
        self._avoidance.update_config(config)

from typing import Any

import socketio

from .. import logger, server
from ..context import Context
from ..recorder import GameRecorder


class BeaconNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to beacon server.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/beacon")
        self.cogip_server = cogip_server
        self.context = Context()
        self.recorder = GameRecorder()

    async def on_connect(self, sid, environ):
        if self.context.beacon_sid:
            message = "A beacon server is already connected"
            logger.error(f"Beacon verser connection refused: {message}")
            raise ConnectionRefusedError(message)
        self.context.beacon_sid = sid

    async def on_connected(self, sid):
        logger.info("Beacon connected.")

    def on_disconnect(self, sid):
        self.context.beacon_sid = None
        logger.info("Beacon disconnected.")

    async def on_register_menu(self, sid, data: dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self.cogip_server.register_menu("beacon", data)

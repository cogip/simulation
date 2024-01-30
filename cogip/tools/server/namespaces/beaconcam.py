from typing import Any

import socketio

from .. import logger
from ..context import Context
from ..recorder import GameRecorder


class BeaconcamNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to beaconcam.
    """

    def __init__(self):
        super().__init__("/beaconcam")
        self._connected = False
        self._context = Context()
        self._recorder = GameRecorder()

    async def on_connect(self, sid, environ):
        if self._connected:
            logger.error("Beaconcam connection refused: a beaconcam is already connected")
            raise ConnectionRefusedError("A beaconcam is already connected")
        self._connected = True

    async def on_connected(self, sid):
        logger.info("Beaconcam connected.")

    def on_disconnect(self, sid):
        self._connected = False
        logger.info("Beaconcam disconnected.")

    async def on_register_menu(self, sid, data: dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self._cogip_server.register_menu("beaconcam", data)

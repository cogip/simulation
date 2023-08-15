from typing import Any

import socketio

from .. import logger, server
from ..context import Context
from ..recorder import GameRecorder


class AvoidanceNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to avoidance.
    """
    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/avoidance")
        self._cogip_server = cogip_server
        self._context = Context()
        self._recorder = GameRecorder()

    async def on_connect(self, sid, environ, auth={}):
        if isinstance(auth, dict) and (robot_id := auth.get("id")):
            if sid not in self._context.avoidance_sids and robot_id in self._context.avoidance_sids.inverse:
                logger.error(f"A avoidance with id '{robot_id}' seems already connected, cleaning up")
                old_sid = self._context.avoidance_sids.inverse[robot_id]
                await self.on_disconnect(old_sid)
        else:
            raise ConnectionRefusedError("Missing 'id' in 'auth' parameter")

    async def on_connected(self, sid, robot_id: int):
        logger.info(f"Avoidance {robot_id} connected.")
        self._context.avoidance_sids[sid] = robot_id

    async def on_disconnect(self, sid):
        if sid in self._context.avoidance_sids:
            robot_id = self._context.avoidance_sids.pop(sid)
            logger.info(f"Avoidance {robot_id} disconnected.")
        else:
            logger.warning(f"Avoidance: attempt to disconnect with unknown sid {sid}.")

    async def on_register_menu(self, sid, data: dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self._cogip_server.register_menu("avoidance", data)

    async def on_config(self, sid, config: dict[str, Any]):
        """
        Callback on config message.
        """
        await self.emit("config", config, namespace="/dashboard")

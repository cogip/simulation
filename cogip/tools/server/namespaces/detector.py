from typing import Any, Dict, List

import socketio

from .. import logger, server
from ..context import Context
from ..recorder import GameRecorder


class DetectorNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to detector.
    """
    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/detector")
        self._cogip_server = cogip_server
        self._detector_sid: str | None = None
        self._context = Context()
        self._recorder = GameRecorder()

    async def on_connect(self, sid, environ, auth={}):
        if self._detector_sid:
            logger.error("Connection refused: a detector is already connected")
            raise ConnectionRefusedError("A detector is already connected")

        if (mode := auth.get("mode")) not in ["detection", "emulation"]:
            logger.error(f"Connection refused: unknown mode '{mode}'")
            raise ConnectionRefusedError(f"Unknown mode '{mode}'")
        self._context.detector_mode = mode
        if mode == "emulation":
            await self.emit("start_lidar_emulation", namespace="/monitor")

        self._detector_sid = sid
        logger.info("Detector connected.")

    async def on_disconnect(self, sid):
        self._detector_sid = None
        if self._context.detector_mode == "emulation":
            await self.emit("stop_lidar_emulation", namespace="/monitor")
        logger.info("Detector disconnected.")

    async def on_register_menu(self, sid, data: Dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self._cogip_server.register_menu("detector", data)

    async def on_obstacles(self, sid, obstacles: List[Dict[str, Any]]):
        """
        Callback on obstacles message.

        Receive a list of obstacles, computed from Lidar data by the Detector.
        These obstacles are sent to planner to compute avoidance path,
        and to monitor/dashboards for display.
        """
        await self.emit("obstacles", obstacles, namespace="/planner")
        await self.emit("obstacles", obstacles, namespace="/dashboard")
        await self._recorder.async_record({"obstacles": obstacles})

    async def on_config(self, sid, config: Dict[str, Any]):
        """
        Callback on config message.
        """
        await self.emit("config", config, namespace="/dashboard")

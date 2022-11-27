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
        self._context = Context()
        self._recorder = GameRecorder()

    async def on_connect(self, sid, environ, auth={}):
        if isinstance(auth, dict) and (robot_id := auth.get("id")):
            if sid not in self._context.detector_sids and robot_id in self._context.detector_sids.inverse:
                raise ConnectionRefusedError(f"A detector with id '{robot_id}' is already connected")
            self._context.detector_sids[sid] = robot_id
            logger.info(f"Detector {robot_id} connected.")
        else:
            raise ConnectionRefusedError("Missing 'id' in 'auth' parameter")

        if (mode := auth.get("mode")) not in ["detection", "emulation"]:
            logger.error(f"Connection refused: unknown mode '{mode}'")
            raise ConnectionRefusedError(f"Unknown mode '{mode}'")
        self._context.detector_modes[robot_id] = mode
        if mode == "emulation":
            await self.emit("start_lidar_emulation", robot_id, namespace="/monitor")

    async def on_disconnect(self, sid):
        robot_id = self._context.detector_sids.pop(sid)
        if self._context.detector_modes[robot_id] == "emulation":
            await self.emit("stop_lidar_emulation", robot_id, namespace="/monitor")
        logger.info(f"Detector {robot_id} disconnected.")

    async def on_register_menu(self, sid, data: Dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self._cogip_server.register_menu("detector", data)

    async def on_obstacles(self, sid, obstacles: List[Dict[str, Any]]):
        """
        Callback on obstacles message.

        Receive a list of obstacles, computed from Lidar data by the Detector.
        These obstacles are sent to planner to compute avoidance path.
        """
        robot_id = self._context.detector_sids[sid]
        await self.emit("obstacles", (robot_id, obstacles), namespace="/planner")
        await self._recorder.async_record({"obstacles": obstacles})

    async def on_config(self, sid, config: Dict[str, Any]):
        """
        Callback on config message.
        """
        await self.emit("config", config, namespace="/dashboard")

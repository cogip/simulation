from typing import Any, Dict, List

import socketio

from .. import logger, server
from ..context import Context
from ..recorder import GameRecorder


class PlannerNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to planner.
    """
    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/planner")
        self._cogip_server = cogip_server
        self._connected = False
        self._context = Context()
        self._recorder = GameRecorder()

    async def on_connect(self, sid, environ):
        if self._connected:
            logger.error("Planner connection refused: a planner is already connected")
            raise ConnectionRefusedError("A planner is already connected")
        self._connected = True
        for robot_id in self._context.connected_robots:
            await self.emit("add_robot", robot_id, namespace="/planner")
        logger.info("Planner connected.")

    def on_disconnect(self, sid):
        self._connected = False
        logger.info("Planner disconnected.")

    async def on_register_menu(self, sid, data: Dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self._cogip_server.register_menu("planner", data)

    async def on_pose_start(self, sid, robot_id: int, pose: Dict[str, Any]):
        """
        Callback on pose start.
        Forward to pose to copilot.
        """
        if robot_id in self._context.copilot_sids.inverse:
            await self.emit("pose_start", pose, to=self._context.copilot_sids.inverse[robot_id], namespace="/copilot")

    async def on_pose_order(self, sid, robot_id: int, pose: Dict[str, Any]):
        """
        Callback on pose order.
        Forward to pose to copilot and dashboards.
        """
        await self.emit("pose_order", pose, to=self._context.copilot_sids.inverse[robot_id], namespace="/copilot")
        await self.emit("pose_order", (robot_id, pose), namespace="/dashboard")
        await self._recorder.async_record({"pose_order": (robot_id, pose)})

    async def on_obstacles(self, sid, obstacles: List[Dict[str, Any]]):
        """
        Callback on obstacles message.

        Receive a list of all obstacles.
        These obstacles are sent to planner to monitor/dashboards for display.
        """
        await self.emit("obstacles", obstacles, namespace="/dashboard")

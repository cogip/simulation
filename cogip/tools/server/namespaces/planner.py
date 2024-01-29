from typing import Any

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

    async def on_connected(self, sid):
        logger.info("Planner connected.")
        for robot_id in self._context.connected_robots:
            virtual = robot_id in self._context.virtual_robots
            await self.emit("add_robot", (robot_id, virtual), namespace="/planner")
            await self.emit("add_robot", (robot_id, virtual), namespace="/dashboard")

    def on_disconnect(self, sid):
        self._connected = False
        logger.info("Planner disconnected.")

    async def on_register_menu(self, sid, data: dict[str, Any]):
        """
        Callback on register_menu.
        """
        await self._cogip_server.register_menu("planner", data)

    async def on_pose_start(self, sid, robot_id: int, pose: dict[str, Any]):
        """
        Callback on pose start.
        Forward to pose to copilot.
        """
        if copilot_sid := self._context.copilot_sids.inverse.get(robot_id):
            await self.emit("pose_start", pose, to=copilot_sid, namespace="/copilot")

    async def on_pose_order(self, sid, robot_id: int, pose: dict[str, Any]):
        """
        Callback on pose order.
        Forward to pose to copilot and dashboards.
        """
        if copilot_sid := self._context.copilot_sids.inverse.get(robot_id):
            await self.emit("pose_order", pose, to=copilot_sid, namespace="/copilot")
        await self.emit("pose_order", (robot_id, pose), namespace="/dashboard")
        await self._recorder.async_record({"pose_order": (robot_id, pose)})

    async def on_obstacles(self, sid, obstacles: list[dict[str, Any]]):
        """
        Callback on obstacles message.

        Receive a list of all obstacles.
        These obstacles are sent to planner to monitor/dashboards for display.
        """
        await self.emit("obstacles", obstacles, namespace="/dashboard")

    async def on_wizard(self, sid, message: list[dict[str, Any]]):
        """
        Callback on wizard message.
        Forward to dashboard.
        """
        message["namespace"] = "/planner"
        await self.emit("wizard", message, namespace="/dashboard")

    async def on_set_controller(self, sid, robot_id, controller: int):
        """
        Callback on set_controller message.
        Forward to copilot.
        """
        await self.emit("set_controller", controller, to=self._context.copilot_sids.inverse[robot_id], namespace="/copilot")

    async def on_path(self, sid, robot_id: int, path: list[dict[str, float]]):
        """
        Callback on robot path.
        Forward the path to dashboard.
        """
        await self.emit("path", (robot_id, path), namespace="/dashboard")
        await self._recorder.async_record({"pose_order": (robot_id, path)})

    async def on_config(self, sid, config: dict[str, Any]):
        """
        Callback on config message.
        """
        await self.emit("config", config, namespace="/dashboard")

    async def on_cmd_reset(self, sid):
        """
        Callback on cmd_reset message.
        """
        await self.emit("cmd_reset", namespace="/monitor")

    async def on_starter_changed(self, sid, robot_id: int, pushed: bool):
        """
        Callback on starter_pushed message.
        """
        await self.emit("starter_changed", (robot_id, pushed), namespace="/monitor")

    async def on_close_wizard(self, sid):
        """
        Callback on close_wizard message.
        """
        await self.emit("close_wizard", namespace="/dashboard")

    async def on_game_start(self, sid):
        """
        Callback on game_start message.
        """
        await self.emit("game_start", namespace="/copilot")

    async def on_game_end(self, sid):
        """
        Callback on game_end message.
        """
        await self.emit("game_end", namespace="/copilot")

    async def on_robot_end(self, sid, robot_id):
        """
        Callback on robot_end message.
        """
        if copilot_sid := self._context.copilot_sids.inverse.get(robot_id):
            await self.emit("game_end", to=copilot_sid, namespace="/copilot")

    async def on_game_reset(self, sid, robot_id):
        """
        Callback on game_reset message.
        """
        if copilot_sid := self._context.copilot_sids.inverse.get(robot_id):
            await self.emit("game_reset", to=copilot_sid, namespace="/copilot")

    async def on_score(self, sid, score: int):
        """
        Callback on score message.
        """
        await self.emit("score", score, namespace="/dashboard")

    async def on_actuator_command(self, sid, data):
        """
        Callback on actuator_command message.
        """
        sid = self._context.copilot_sids.inverse[data["robot_id"]]
        await self.emit("actuator_command", data=data["command"], to=sid, namespace="/copilot")

    async def on_start_video_record(self, sid):
        await self.emit("start_video_record", namespace="/robotcam")
        await self.emit("start_video_record", namespace="/beaconcam")

    async def on_stop_video_record(self, sid):
        await self.emit("stop_video_record", namespace="/robotcam")
        await self.emit("stop_video_record", namespace="/beaconcam")

    async def on_brake(self, sid, robot_id):
        """
        Callback on brake message.
        """
        if copilot_sid := self._context.copilot_sids.inverse.get(robot_id):
            await self.emit("brake", to=copilot_sid, namespace="/copilot")

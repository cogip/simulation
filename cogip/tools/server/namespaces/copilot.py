from typing import Any

import socketio

from cogip import models
from .. import logger, server
from ..context import Context
from ..recorder import GameRecorder


class CopilotNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to copilot.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/copilot")
        self._cogip_server = cogip_server
        self._context = Context()
        self._recorder = GameRecorder()

    async def on_connect(self, sid, environ, auth={}):
        if isinstance(auth, dict) and (robot_id := auth.get("id")):
            if sid not in self._context.copilot_sids and robot_id in self._context.copilot_sids.inverse:
                logger.error(f"A copilot with id '{robot_id}' seems already connected, cleaning up")
                old_sid = self._context.copilot_sids.inverse[robot_id]
                await self.on_disconnect(old_sid)
        else:
            raise ConnectionRefusedError("Missing 'id' in 'auth' parameter")

    async def on_connected(self, sid, robot_id: int, virtual: bool):
        logger.info(f"Copilot {robot_id} connected.")
        self._context.copilot_sids[sid] = robot_id
        self._context.connected_robots.append(robot_id)
        if virtual:
            self._context.virtual_robots.append(robot_id)
        await self.emit("add_robot", (robot_id, virtual), namespace="/planner")
        await self.emit("add_robot", (robot_id, virtual), namespace="/dashboard")

    async def on_disconnect(self, sid):
        if sid in self._context.copilot_sids:
            robot_id = self._context.copilot_sids.pop(sid)
            self._context.connected_robots.remove(robot_id)
            if robot_id in self._context.virtual_robots:
                self._context.virtual_robots.remove(robot_id)
            if robot_id in self._context.shell_menu:
                del self._context.shell_menu[robot_id]
            await self.emit("del_robot", robot_id, namespace="/planner")
            await self.emit("del_robot", robot_id, namespace="/dashboard")
            logger.info(f"Copilot {robot_id} disconnected.")
        else:
            logger.warning(f"Copilot: attempt to disconnect with unknown sid {sid}.")

    async def on_reset(self, sid) -> None:
        """
        Callback on reset event.
        """
        if sid not in self._context.copilot_sids:
            return
        robot_id = self._context.copilot_sids[sid]
        await self.emit("reset", robot_id, namespace="/planner")
        await self._recorder.async_do_rollover()
        self._recorder.recording = True

    async def on_register_menu(self, sid, data: dict[str, Any]):
        """
        Callback on register_menu.
        """
        robot_id = self._context.copilot_sids[sid]
        data["menu"]["name"] = f"{data['menu']['name']} {robot_id}"
        await self._cogip_server.register_menu(f"copilot/{robot_id}", data)

    async def on_pose_reached(self, sid) -> None:
        """
        Callback on pose reached message.
        """
        if not (robot_id := self._context.copilot_sids.get(sid)):
            return
        await self.emit("pose_reached", robot_id, namespace="/planner")

    async def on_menu(self, sid, menu):
        """
        Callback on menu event.
        """
        if not (robot_id := self._context.copilot_sids.get(sid)):
            return
        self._context.shell_menu[robot_id] = models.ShellMenu.model_validate(menu)
        await self.emit("shell_menu", (robot_id, menu), namespace="/dashboard")

    async def on_pose(self, sid, pose):
        """
        Callback on pose event.
        """
        if not (robot_id := self._context.copilot_sids.get(sid)):
            return
        detector_sid = self._context.detector_sids.inverse.get(robot_id)
        if detector_sid:  # Detector may not be already connected
            await self.emit("pose_current", pose, to=detector_sid, namespace="/detector")
        await self.emit("pose_current", (robot_id, pose), namespace="/planner")
        await self.emit("pose_current", (robot_id, pose), namespace="/dashboard")
        await self._recorder.async_record({"pose_current": (robot_id, pose)})

    async def on_state(self, sid, state):
        """
        Callback on state event.
        """
        if not (robot_id := self._context.copilot_sids.get(sid)):
            return
        await self.emit("state", (robot_id, state), namespace="/dashboard")
        await self._recorder.async_record({"state": (robot_id, state)})

    async def on_actuators_state(self, sid, actuators_state: dict[str, Any]):
        """
        Callback on actuators_state message.
        """
        await self.emit("actuators_state", actuators_state, namespace="/dashboard")

    async def on_pid(self, sid, pid: dict[str, Any]):
        """
        Callback on pid message.
        """
        await self.emit("pid", pid, namespace="/dashboard")

    async def on_config(self, sid, config: dict[str, Any]):
        """
        Callback on config message.
        """
        await self.emit("config", config, namespace="/dashboard")

    async def on_game_end(self, sid) -> None:
        """
        Callback on game end message.
        """
        robot_id = self._context.copilot_sids[sid]
        await self.emit("game_end", robot_id, namespace="/planner")

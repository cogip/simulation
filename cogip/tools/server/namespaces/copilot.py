import socketio

from cogip import models
from .. import logger
from ..context import Context
from ..recorder import GameRecorder


class CopilotNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to copilot.
    """
    def __init__(self):
        super().__init__("/copilot")
        self._context = Context()
        self._recorder = GameRecorder()

    async def on_connect(self, sid, environ, auth={}):
        if isinstance(auth, dict) and (robot_id := auth.get("id")):
            if sid not in self._context.copilot_sids and robot_id in self._context.copilot_sids.inverse:
                raise ConnectionRefusedError(f"A copilot with id '{robot_id}' is already connected")
            self._context.copilot_sids[sid] = robot_id
            self._context.connected_robots.append(robot_id)
            await self.emit("add_robot", robot_id, namespace="/planner")
            await self.emit("add_robot", robot_id, namespace="/dashboard")

            logger.info(f"Copilot {robot_id} connected.")
        else:
            raise ConnectionRefusedError("Missing 'id' in 'auth' parameter")

    async def on_disconnect(self, sid):
        robot_id = self._context.copilot_sids.pop(sid)
        self._context.connected_robots.remove(robot_id)
        del self._context.shell_menu[robot_id]
        await self.emit("del_robot", robot_id, namespace="/planner")
        await self.emit("del_robot", robot_id, namespace="/dashboard")
        logger.info(f"Copilot {robot_id} disconnected.")

    async def on_reset(self, sid) -> None:
        """
        Callback on reset event.
        """
        robot_id = self._context.copilot_sids[sid]
        await self.emit("reset", robot_id, namespace="/planner")
        await self._recorder.async_do_rollover()

    async def on_pose_reached(self, sid) -> None:
        """
        Callback on pose reached message.
        """
        robot_id = self._context.copilot_sids[sid]
        await self.emit("pose_reached", robot_id, namespace="/planner")

    async def on_menu(self, sid, menu):
        """
        Callback on menu event.
        """
        robot_id = self._context.copilot_sids[sid]
        self._context.shell_menu[robot_id] = models.ShellMenu.parse_obj(menu)
        await self.emit("shell_menu", (robot_id, menu), namespace="/dashboard")

    async def on_pose(self, sid, pose):
        """
        Callback on pose event.
        """
        robot_id = self._context.copilot_sids[sid]
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
        robot_id = self._context.copilot_sids[sid]
        await self.emit("state", (robot_id, state), namespace="/dashboard")
        if state.get("mode", 0):
            self._recorder.recording = True
        await self._recorder.async_record({"state": (robot_id, state)})

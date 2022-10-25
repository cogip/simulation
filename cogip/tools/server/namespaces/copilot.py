import socketio

from .. import logger
from ..context import Context
from ..recorder import GameRecorder


class CopilotNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to copilot.
    """
    def __init__(self):
        super().__init__("/copilot")
        self._copilot_sid: str | None = None
        self._context = Context()
        self._recorder = GameRecorder()

    async def on_connect(self, sid, environ):
        if self._copilot_sid:
            logger.error("Connection refused: a copilot is already connected")
            raise ConnectionRefusedError("A copilot is already connected")
        self._copilot_sid = sid
        logger.info("Copilot connected.")

    def on_disconnect(self, sid):
        self._copilot_sid = None
        logger.info("Copilot disconnected.")

    async def on_reset(self, sid) -> None:
        """
        Callback on reset event.
        """
        await self.emit("reset", namespace="/planner")
        await self._recorder.async_do_rollover()

    async def on_pose_reached(self, sid) -> None:
        """
        Callback on pose reached message.
        """
        await self.emit("pose_reached", namespace="/planner")

    async def on_menu(self, sid, menu):
        """
        Callback on menu event.
        """
        self._context.shell_menu = menu
        await self.emit("shell_menu", menu, namespace="/dashboard")

    async def on_pose(self, sid, pose):
        """
        Callback on pose event.
        """
        await self.emit("pose_current", pose, namespace="/detector")
        await self.emit("pose_current", pose, namespace="/planner")
        await self.emit("pose_current", pose, namespace="/dashboard")
        await self._recorder.async_record({"pose_current": pose})

    async def on_state(self, sid, state):
        """
        Callback on state event.
        """
        await self.emit("state", state, namespace="/dashboard")
        if state.get("mode", 0):
            self._recorder.recording = True
        await self._recorder.async_record({"state": state})

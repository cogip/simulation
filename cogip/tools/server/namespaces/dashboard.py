import socketio

from .. import logger
from ..context import Context


class DashboardNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to dashboards.
    """
    def __init__(self):
        super().__init__("/dashboard")
        self._context = Context()

    async def on_connect(self, sid, environ):
        logger.info("Dashboard connected.")
        if self._context.planner_menu:
            await self.emit("planner_menu", self._context.planner_menu, to=sid)
        if self._context.shell_menu:
            await self.emit("shell_menu", self._context.shell_menu, to=sid)

    def on_disconnect(self, sid):
        logger.info("Dashboard disconnected.")

    async def on_planner_cmd(self, sid, cmd: str) -> None:
        """
        Callback on planner command message from dashboard.
        """
        await self.emit("command", cmd, namespace="/planner")

    async def on_shell_cmd(self, sid, cmd: str) -> None:
        """
        Callback on shell command message from dashboard.
        """
        await self.emit("command", cmd, namespace="/copilot")

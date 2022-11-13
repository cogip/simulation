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
        await self.emit("tool_menu", self._context.tool_menus[self._context.current_tool_menu].dict(), to=sid)
        if self._context.shell_menu:
            await self.emit("shell_menu", self._context.shell_menu, to=sid)

    def on_disconnect(self, sid):
        logger.info("Dashboard disconnected.")

    async def on_tool_cmd(self, sid, cmd: str) -> None:
        """
        Callback on tool command message from dashboard.
        """
        # Find entry in current menu
        entry = None
        for entry in self._context.tool_menus[self._context.current_tool_menu].entries:
            if entry.cmd == cmd:
                break

        # Check if it corresponds to a menu or a command
        if entry and entry.cmd in self._context.tool_menus:
            # Enter a menu
            self._context.current_tool_menu = cmd
            await self.emit(
                "tool_menu",
                self._context.tool_menus[self._context.current_tool_menu].dict(),
                namespace="/dashboard"
            )
        else:
            # Forward command to corresponding namespace
            if cmd == "exit":
                self._context.current_tool_menu = "root"
                await self.emit(
                    "tool_menu",
                    self._context.tool_menus[self._context.current_tool_menu].dict(),
                    namespace="/dashboard"
                )
            else:
                namespace, _, _ = self._context.current_tool_menu.partition("/")
                await self.emit("command", cmd, namespace=f"/{namespace}")

    async def on_shell_cmd(self, sid, cmd: str) -> None:
        """
        Callback on shell command message from dashboard.
        """
        await self.emit("command", cmd, namespace="/copilot")

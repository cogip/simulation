from typing import Any, Dict
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
        pass

    async def on_connected(self, sid):
        logger.info("Dashboard connected.")
        await self.emit("tool_menu", self._context.tool_menus[self._context.current_tool_menu].dict(), to=sid)
        for robot_id, menu in self._context.shell_menu.items():
            await self.emit("shell_menu", (robot_id, menu.dict()), to=sid)
        for robot_id in self._context.connected_robots:
            await self.emit("add_robot", (robot_id, robot_id in self._context.virtual_robots), to=sid)

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
                split_ns = self._context.current_tool_menu.split("/")
                namespace = split_ns.pop(0)
                if namespace == "copilot":
                    robot_id = int(split_ns.pop(0))
                    sid = self._context.copilot_sids.inverse[robot_id]
                    await self.emit("command", cmd, to=sid, namespace="/copilot")
                else:
                    await self.emit("command", cmd, namespace=f"/{namespace}")

    async def on_shell_cmd(self, sid, robot_id: int, cmd: str) -> None:
        """
        Callback on shell command message from dashboard.
        """
        await self.emit("shell_command", cmd, to=self._context.copilot_sids.inverse[robot_id], namespace="/copilot")

    async def on_config_updated(self, sid, config: Dict[str, Any]) -> None:
        namespace = config.pop("namespace")
        await self.emit("config_updated", config, namespace=namespace)

    async def on_actuators_stop(self, sid, robot_id):
        """
        Callback on actuators_stop message.
        """
        sid = self._context.copilot_sids.inverse[robot_id]
        await self.emit("actuators_stop", to=sid, namespace="/copilot")

    async def on_actuator_command(self, sid, data):
        """
        Callback on actuator_command message.
        """
        sid = self._context.copilot_sids.inverse[data["robot_id"]]
        await self.emit("actuator_command", data=data["command"], to=sid, namespace="/copilot")

    async def on_wizard(self, sid, data: dict[str, Any]):
        """
        Callback on wizard message.
        """
        namespace = data.pop("namespace")
        await self.emit("wizard", data, namespace=namespace)
        await self.emit("close_wizard")

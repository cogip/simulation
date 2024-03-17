import socketio

from .. import logger, server
from ..menu import menu


class DashboardNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to Beacon dashboard.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/dashboard")
        self.cogip_server = cogip_server

    def on_connect(self, sid, environ):
        pass

    async def on_connected(self, sid):
        logger.info("Dashboard connected.")
        for robot_id, robot in self.cogip_server.robots.items():
            if robot.sio.connected:
                await self.cogip_server.sio.emit("add_robot", robot_id, namespace="/dashboard")
        await self.emit(
            "tool_menu",
            menu.model_dump(),
            namespace="/dashboard",
        )

    def on_disconnect(self, sid):
        logger.info("Dashboard disconnected.")

    async def on_tool_cmd(self, sid, cmd: str):
        match cmd:
            case "reset":
                for _, robot in self.cogip_server.robots.items():
                    if robot.sio.connected:
                        await robot.sio.emit("reset", namespace="/beacon")
            case "start":
                for _, robot in self.cogip_server.robots.items():
                    if robot.sio.connected:
                        await robot.sio.emit("command", "play", namespace="/beacon")
            case _:
                logger.warning(f"Unknown command: {cmd}")

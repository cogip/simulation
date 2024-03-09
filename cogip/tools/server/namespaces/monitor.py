import socketio

from .. import logger, server
from ..context import Context


class MonitorNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to monitor.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/monitor")
        self.cogip_server = cogip_server
        self.context = Context()
        self.context.monitor_sid = None

    async def on_connect(self, sid, environ):
        if self.context.monitor_sid:
            message = "A monitor is already connected"
            logger.error(f"Monitor connection refused: {message}")
            raise ConnectionRefusedError(message)
        self.context.monitor_sid = sid

    async def on_connected(self, sid):
        logger.info("Monitor connected.")
        await self.emit("add_robot", (self.context.robot_id, self.context.virtual), namespace="/monitor")
        if self.context.virtual:
            await self.emit("start_lidar_emulation", self.context.robot_id, namespace="/monitor")

    def on_disconnect(self, sid):
        self.context.monitor_sid = None
        logger.info("Monitor disconnected.")

    async def on_lidar_data(self, sid, lidar_data: list[int]):
        """
        Callback on lidar data.

        In emulation mode, receive Lidar data from the Monitor,
        and forward to the Detector in charge of computing dynamic obstacles.
        """
        await self.emit("lidar_data", lidar_data, namespace="/detector")

    async def on_starter_changed(self, sid, pushed: bool):
        """
        Callback on starter_changed message.
        """
        await self.emit("starter_changed", pushed, namespace="/planner")

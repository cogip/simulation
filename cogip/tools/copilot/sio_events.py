from typing import Any, Dict

import socketio

from cogip import models
from . import copilot, logger
from .messages import PB_Command, PB_PathPose


class SioEvents(socketio.AsyncClientNamespace):
    """
    Handle all SocketIO events received by Planner.
    """

    def __init__(self, copilot: "copilot.Copilot"):
        super().__init__("/copilot")
        self._copilot = copilot

    async def on_connect(self):
        """
        On connection to cogip-server.
        """
        logger.info("Connected to cogip-server")
        if self._copilot.shell_menu:
            await self.emit("menu", copilot.shell_menu.dict(exclude_defaults=True, exclude_unset=True))

    def on_disconnect(self) -> None:
        """
        On disconnection from cogip-server.
        """
        logger.info("Disconnected from cogip-server")

    async def on_connect_error(self, data: Dict[str, Any]) -> None:
        """
        On connection error, check if a Planner is already connected and exit,
        or retry connection.
        """
        logger.error(f"Connection to cogip-server failed: {data.get('message')}")

    async def on_command(self, data):
        """
        Callback on shell command message.

        Build the Protobuf command message:

        * split received string at first space if any.
        * first is the command and goes to `cmd` attribute.
        * second part is arguments, if any, and goes to `desc` attribute.
        """
        response = PB_Command()
        response.cmd, _, response.desc = data.partition(" ")
        await self._copilot.pbcom.send_serial_message(copilot.command_uuid, response)

    async def on_pose_start(self, data: Dict[str, Any]):
        """
        Callback on pose start (from planner).
        Forward to mcu-firmware.
        """
        start_pose = models.PathPose.parse_obj(data)
        pb_start_pose = PB_PathPose()
        start_pose.copy_pb(pb_start_pose)
        await self._copilot.pbcom.send_serial_message(copilot.pose_start_uuid, pb_start_pose)

    async def on_pose_order(self, data: Dict[str, Any]):
        """
        Callback on pose order (from planner).
        Forward to mcu-firmware.
        """
        pose_order = models.PathPose.parse_obj(data)
        pb_pose_order = PB_PathPose()
        pose_order.copy_pb(pb_pose_order)
        await self._copilot.pbcom.send_serial_message(copilot.pose_order_uuid, pb_pose_order)

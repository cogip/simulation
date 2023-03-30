import asyncio
import platform
from typing import Any, Dict

import polling2
from pydantic import parse_obj_as
import socketio

from cogip import models
from cogip.models.actuators import ServoCommand, PumpCommand, ActuatorCommand
from . import copilot, logger
from .menu import menu
from .messages import PB_ActuatorCommand, PB_Command, PB_PathPose, PB_Controller
from .pid import PidEnum


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
        await asyncio.to_thread(
            polling2.poll,
            lambda: self.client.connected is True,
            step=1,
            poll_forever=True
        )
        logger.info("Connected to cogip-server")
        await self.emit("connected", (self._copilot.id, (platform.machine() != "aarch64")))

        if self._copilot.shell_menu:
            await self.emit("menu", self._copilot.shell_menu.dict(exclude_defaults=True, exclude_unset=True))
        await self.emit("register_menu", {"name": "copilot", "menu": menu.dict()})

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
        Callback on tool command message.
        """
        cmd, _, _ = data.partition(" ")
        match cmd:
            case "actuators_control":
                # Start thread emitting actuators status
                await self._copilot.pbcom.send_serial_message(copilot.actuators_thread_start_uuid, None)
            case "pid_config":
                # Request pid state
                await self._copilot.pbcom.send_serial_message(copilot.pid_request_uuid, None)
            case _:
                logger.warning(f"Unknown command: {cmd}")

    async def on_shell_command(self, data):
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

    async def on_actuators_stop(self):
        """
        Callback on actuators_stop (from dashboard).
        Forward to mcu-firmware.
        """
        await self._copilot.pbcom.send_serial_message(copilot.actuators_thread_stop_uuid, None)

    async def on_actuator_command(self, data: Dict[str, Any]):
        """
        Callback on actuator_command (from dashboard).
        Forward to mcu-firmware.
        """
        command = parse_obj_as(ActuatorCommand, data)

        pb_command = PB_ActuatorCommand()
        if isinstance(command, ServoCommand):
            command.pb_copy(pb_command.servo)
        elif isinstance(command, PumpCommand):
            command.pb_copy(pb_command.pump)
        await self._copilot.pbcom.send_serial_message(copilot.actuators_command_uuid, pb_command)

    async def on_config_updated(self, config: Dict[str, Any]) -> None:
        """
        Callback on config_updated from dashboard.
        Update pid PB message and send it back to firmware.
        """
        parent, _, name = config["name"].partition("/")
        if parent and name:
            setattr(self._copilot._pb_pids.pids[PidEnum[parent]], name, config["value"])
            await self._copilot.pbcom.send_serial_message(copilot.pid_uuid, self._copilot._pb_pids)

    async def on_set_controller(self, controller: int):
        """
        Callback on set_controller message.
        Forward to firmware.
        """
        pb_controller = PB_Controller()
        pb_controller.id = controller
        await self._copilot.pbcom.send_serial_message(copilot.controller_uuid, pb_controller)

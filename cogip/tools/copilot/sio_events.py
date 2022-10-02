from typing import Any, Dict, List

from pydantic import parse_obj_as
import socketio
from socketio.exceptions import ConnectionRefusedError

from cogip import models
from .messages import PB_Command, PB_Obstacles
from . import server


class SioEvents(socketio.AsyncNamespace):
    def __init__(self, copilot: "server.CopilotServer"):
        super().__init__()
        self._copilot = copilot

    async def on_connect(self, sid, environ, auth):
        """
        Callback on new monitor connection.

        Send the current menu to monitors.
        """
        if auth and isinstance(auth, dict) and (client_type := auth.get("type")):
            if client_type == "monitor":
                if self._copilot.monitor_sid:
                    print("Connection refused: a monitor is already connected")
                    raise ConnectionRefusedError("A monitor is already connected")
                self._copilot.monitor_sid = sid
            if client_type == "planner":
                if self._copilot.planner_sid:
                    print("Connection refused: a planner is already connected")
                    raise ConnectionRefusedError("A planner is already connected")
                self._copilot.planner_sid = sid

            if client_type in ["monitor", "dashboard"]:
                self.enter_room(sid, "dashboards")
                print("Client invited to room 'dashboards'.")
                await self._copilot.emit_menu(sid)
            if client_type == "detector":
                if self._copilot.detector_sid:
                    print("Connection refused: a detector is already connected")
                    raise ConnectionRefusedError("A detector is already connected")
                if (mode := auth.get("mode")) not in ["detection", "emulation"]:
                    print(f"Connection refused: unknown mode '{mode}'")
                    raise ConnectionRefusedError(f"Unknown mode '{mode}'")
                self._copilot.detector_sid = sid
                self._copilot.detector_mode = mode
                if mode == "emulation" and self._copilot.monitor_sid is not None:
                    await self.emit("start_lidar_emulation", to=self._copilot.monitor_sid)

    async def on_disconnect(self, sid):
        """
        Callback on monitor disconnection.
        """
        if sid == self._copilot.monitor_sid:
            self._copilot.monitor_sid = None
            if self._copilot.detector_mode == "emulation":
                await self.emit("stop_lidar_emulation", to=self._copilot.monitor_sid)
        elif sid == self._copilot.detector_sid:
            self._copilot.detector_sid = None
        elif sid == self._copilot.planner_sid:
            self._copilot.planner_sid = None
        self.leave_room(sid, "dashboards")

    async def on_cmd(self, sid, data):
        """
        Callback on command message.

        Receive a command from a monitor.

        Build the Protobuf command message:

        * split received string at first space if any.
        * first is the command and goes to `cmd` attribute.
        * second part is arguments, if any, and goes to `desc` attribute.
        """
        response = PB_Command()
        response.cmd, _, response.desc = data.partition(" ")
        await self._copilot.send_serial_message(server.command_uuid, response)

    async def on_obstacles(self, sid, obstacles: List[Dict[str, Any]]):
        """
        Callback on obstacles message.

        Receive a list of obstacles, computed from Lidar data by the Detector.
        These obstacles are sent to mcu-firmware to compute avoidance path,
        and to monitor/dashboards for display.
        """
        dyn_obstacles = parse_obj_as(models.DynObstacleList, obstacles)
        pb_obstacles = PB_Obstacles()
        for dyn_obstacle in dyn_obstacles:
            if isinstance(dyn_obstacle, models.DynRoundObstacle):
                pb_obstacle = pb_obstacles.circles.add()
                pb_obstacle.x = int(dyn_obstacle.x)
                pb_obstacle.y = int(dyn_obstacle.y)
                pb_obstacle.radius = int(dyn_obstacle.radius)
        await self._copilot.send_serial_message(server.obstacles_uuid, pb_obstacles)
        await self.emit("obstacles", obstacles, room="dashboards")

    async def on_lidar_data(self, sid, lidar_data):
        """
        Callback on lidar data.

        In emulation mode, receive Lidar data from the Monitor,
        and forward to the Detector in charge of computing dynamic obstacles.
        """
        if self._copilot.detector_sid:
            await self.emit("lidar_data", lidar_data, to=self._copilot.detector_sid)

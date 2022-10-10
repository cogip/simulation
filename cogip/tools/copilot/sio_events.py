from typing import Any, Dict, List

import socketio
from socketio.exceptions import ConnectionRefusedError

from cogip import models
from .messages import PB_Command, PB_PathPose
from . import server


class SioEvents(socketio.AsyncNamespace):
    def __init__(self, copilot: "server.CopilotServer"):
        super().__init__()
        self._copilot = copilot

    async def on_connect(self, sid, environ, auth):
        """
        Callback on new monitor connection.

        Send the current menus to dashboards.
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
                await self._copilot.emit_shell_menu(sid)
                await self._copilot.emit_planner_menu(sid)
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

    async def on_shell_cmd(self, sid, data):
        """
        Callback on shell command message.

        Receive a shell command from a dashboard.

        Build the Protobuf command message:

        * split received string at first space if any.
        * first is the command and goes to `cmd` attribute.
        * second part is arguments, if any, and goes to `desc` attribute.
        """
        response = PB_Command()
        response.cmd, _, response.desc = data.partition(" ")
        await self._copilot.send_serial_message(server.command_uuid, response)

    async def on_planner_cmd(self, sid, data):
        """
        Callback on planner command message.

        Receive a planner command from a dashboard and forward it to the planner.
        """
        await self.emit("command", data, self._copilot.planner_sid)

    async def on_obstacles(self, sid, obstacles: List[Dict[str, Any]]):
        """
        Callback on obstacles message (from detector only).

        Receive a list of obstacles, computed from Lidar data by the Detector.
        These obstacles are sent to planner to compute avoidance path,
        and to monitor/dashboards for display.
        """
        if sid != self._copilot.detector_sid:
            return

        await self.emit("obstacles", obstacles, to=self._copilot.planner_sid)
        await self.emit("obstacles", obstacles, room="dashboards")

    async def on_lidar_data(self, sid, lidar_data):
        """
        Callback on lidar data (from monitor only).

        In emulation mode, receive Lidar data from the Monitor,
        and forward to the Detector in charge of computing dynamic obstacles.
        """
        if sid != self._copilot.monitor_sid:
            return

        if self._copilot.detector_sid:
            await self.emit("lidar_data", lidar_data, to=self._copilot.detector_sid)

    async def on_planner_menu(self, sid, menu):
        """
        Callback on planner menu (from planner only).
        """
        if sid != self._copilot.planner_sid:
            return

        self._copilot.planner_menu = models.ShellMenu.parse_obj(menu)
        await self._copilot.emit_planner_menu("dashboards")

    async def on_start_pose(self, sid, data: Dict[str, Any]):
        """
        Callback on start pose (from planner only).
        Forward to pose to mcu-firmware and dashboards.
        """
        if sid != self._copilot.planner_sid:
            return

        start_pose = models.PathPose.parse_obj(data)
        pb_start_pose = PB_PathPose()
        start_pose.copy_pb(pb_start_pose)
        await self._copilot.send_serial_message(server.start_pose_uuid, pb_start_pose)
        await self.emit("pose_order", data, room="dashboards")

    async def on_pose_to_reach(self, sid, data: Dict[str, Any]):
        """
        Callback on pose to reach (from planner only).
        Forward to pose to mcu-firmware and dashboards.
        """
        if sid != self._copilot.planner_sid:
            return

        pose_to_reach = models.PathPose.parse_obj(data)
        pb_pose_to_reach = PB_PathPose()
        pose_to_reach.copy_pb(pb_pose_to_reach)
        await self._copilot.send_serial_message(server.pose_uuid, pb_pose_to_reach)
        await self.emit("pose_order", data, room="dashboards")

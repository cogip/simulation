import socketio
from socketio.exceptions import ConnectionRefusedError

from .messages import PB_Command, PB_Wizard
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

            if client_type in ["monitor", "dashboard"]:
                self.enter_room(sid, "dashboards")
                print("Client invited to room 'dashboards'.")
                await self._copilot.emit_menu(sid)

    async def on_disconnect(self, sid):
        """
        Callback on monitor disconnection.
        """
        if sid == self._copilot.monitor_sid:
            self._copilot.monitor_sid = None
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

    async def on_wizard(self, sid, data):
        """
        Callback on Wizard message.

        Receive a command from a monitor.

        Build the Protobuf wizard message and send to firmware.
        """
        await self.sio.emit("close_wizard")

        response = PB_Wizard()
        response.name = data["name"]
        data_type = data["type"]
        if not isinstance(data["value"], list):
            value = getattr(response, data_type).value
            value_type = type(value)
            getattr(response, data_type).value = value_type(data["value"])
        elif data_type == "select_integer":
            response.select_integer.value[:] = [int(v) for v in data["value"]]
        elif data_type == "select_floating":
            response.select_floating.value[:] = [float(v) for v in data["value"]]
        elif data_type == "select_str":
            response.select_str.value[:] = data["value"]

        await self._copilot.send_serial_message(server.wizard_uuid, response)

    async def on_sample(self, sid, data):
        self._copilot.set_samples(data)

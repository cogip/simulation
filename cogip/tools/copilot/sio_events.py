import socketio

from .messages import PB_Command, PB_Wizard
from . import server


class SioEvents(socketio.AsyncNamespace):
    def __init__(self, copilot: "server.CopilotServer"):
        super().__init__()
        self._copilot = copilot

    async def on_connect(self, sid, environ):
        """
        Callback on new monitor connection.

        Send the current menu to monitors.
        """
        self._copilot.sio_client_connected()
        await self._copilot.emit_menu()

    async def on_disconnect(self, sid):
        """
        Callback on monitor disconnection.
        """
        self._copilot.sio_client_disconnected()

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

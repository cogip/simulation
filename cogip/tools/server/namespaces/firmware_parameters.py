from typing import Any

import socketio

from .. import logger, server


class FirmwareParametersNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to firmware parameter clients.
    Supports multiple simultaneous client connections.
    """

    def __init__(self, cogip_server: "server.Server"):
        super().__init__("/parameters")
        self.cogip_server = cogip_server

    async def on_get_parameter_value(self, sid, data: dict[str, Any]):
        """
        Callback on get_parameter_value message.
        Forward to copilot.
        """
        logger.info(f"[parameters => copilot] Get parameter: {data}")
        await self.emit("get_parameter_value", data, namespace="/copilot")

    async def on_set_parameter_value(self, sid, data: dict[str, Any]):
        """
        Callback on set_parameter_value message.
        Forward to copilot.
        """
        logger.info(f"[parameters => copilot] Set parameter: {data}")
        await self.emit("set_parameter_value", data, namespace="/copilot")

    async def on_reset_parameter_value(self, sid, data: dict[str, Any]):
        """
        Callback on reset_parameter_value message.
        Forward to copilot.
        """
        logger.info(f"[parameters => copilot] Reset parameter: {data}")
        await self.emit("reset_parameter_value", data, namespace="/copilot")

    async def on_get_parameter_groups(self, sid):
        """
        Callback on get_parameter_groups message.
        Forward to copilot.
        """
        logger.info("[parameters => copilot] Get parameter groups")
        await self.emit("get_parameter_groups", namespace="/copilot")

    async def on_list_parameters(self, sid, name: str):
        """
        Callback on list_parameters message.
        Forward to copilot.
        """
        logger.info(f"[parameters => copilot] List parameters: {name}")
        await self.emit("list_parameters", name, namespace="/copilot")

    async def on_get_parameter_definition(self, sid, key_hash: int):
        """
        Callback on get_parameter_definition message.
        Forward to copilot.
        """
        logger.info(f"[parameters => copilot] Get parameter definition: 0x{key_hash:08x}")
        await self.emit("get_parameter_definition", key_hash, namespace="/copilot")

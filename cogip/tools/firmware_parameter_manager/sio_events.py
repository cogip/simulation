from typing import TYPE_CHECKING, Any

import socketio
from google.protobuf.json_format import ParseDict

from cogip.models import FirmwareParameter
from cogip.protobuf import (
    PB_ParameterGetResponse,
    PB_ParameterGroup,
    PB_ParameterListResponse,
    PB_ParameterResetResponse,
    PB_ParameterSetResponse,
)

if TYPE_CHECKING:
    from .firmware_parameter_manager import FirmwareParameterManager


class SioEvents(socketio.AsyncClientNamespace):
    """
    Handle all SocketIO events received by FirmwareParameterManager.
    """

    def __init__(self, manager: "FirmwareParameterManager"):
        super().__init__("/parameters")
        self.manager = manager
        self.connected = False

    async def on_connect(self):
        self.connected = True

    async def on_disconnect(self):
        self.connected = False

    async def on_parameter_groups(self, data: list[dict[str, Any]]):
        """
        Handle the parameter registries announced by the firmware, kept by copilot.
        """
        groups = [ParseDict(group, PB_ParameterGroup()) for group in data]
        self.manager.resolve("parameter_groups", 0, groups)

    async def on_list_parameters_response(self, data: dict[str, Any]):
        """
        Handle the key hash of a listed parameter, ignored if no registry is being listed by this client.
        """
        if self.manager.key_hashes is not None:
            self.manager.key_hashes.put_nowait(ParseDict(data, PB_ParameterListResponse()).key_hash)

    async def on_parameter_definition(self, data: dict[str, Any]):
        """
        Handle the definition of a parameter, matched to its request by key hash.
        """
        parameter = FirmwareParameter.model_validate(data)
        self.manager.resolve("parameter_definition", hash(parameter), parameter)

    async def on_get_parameter_response(self, data: dict[str, Any]):
        response = ParseDict(data, PB_ParameterGetResponse())
        self.manager.resolve("get_parameter_response", response.key_hash, response)

    async def on_set_parameter_response(self, data: dict[str, Any]):
        response = ParseDict(data, PB_ParameterSetResponse())
        self.manager.resolve("set_parameter_response", response.key_hash, response)

    async def on_reset_parameter_response(self, data: dict[str, Any]):
        response = ParseDict(data, PB_ParameterResetResponse())
        self.manager.resolve("reset_parameter_response", response.key_hash, response)

import asyncio
from typing import Any

import socketio

from cogip.models import FirmwareParameter
from cogip.protobuf import PB_ParameterGroup
from cogip.utils.fnv1a import fnv1a_hash_bytes
from . import logger
from .sio_events import SioEvents


class FirmwareParameterManager:
    """
    Manager to access the firmware parameters via SocketIO through copilot.

    This class is designed to be embedded into another Socket.IO client. It registers its own
    namespace (/parameters) on the provided client, the host tool manages the connection.

    The parameters are discovered with `discover()`: each board announces its parameter
    registry to copilot, which keeps it, then the manager lists the key hashes of each registry
    and gets the definition of each parameter.
    Requests address a parameter by the FNV-1a hash of its name, and their responses are
    matched to them by this hash.
    """

    def __init__(self, sio: socketio.AsyncClient):
        """
        Args:
            sio: External Socket.IO client on which to register the /parameters namespace.
        """
        self.sio = sio
        self.sio_events = SioEvents(self)
        self.sio.register_namespace(self.sio_events)

        # Discovered parameters, by registry and by name
        self.registries: dict[str, list[FirmwareParameter]] = {}
        self.parameters: dict[str, FirmwareParameter] = {}

        # Futures of the requests waiting for their response, by response event and key hash
        self.pending_requests: dict[tuple[str, int], asyncio.Future] = {}

        # Key hashes received for the registry being listed
        self.key_hashes: asyncio.Queue[int] | None = None

    @property
    def namespace(self) -> str:
        """Return the namespace path to include when connecting the host client."""
        return self.sio_events.namespace

    @property
    def is_connected(self) -> bool:
        """Check if the namespace is connected and ready."""
        return self.sio_events.connected

    async def discover(self, timeout: float = 1) -> None:
        """
        Discovers the parameters of the registries announced by the firmware.

        A registry whose parameters are not received as announced is left out.

        Raises:
            TimeoutError: If copilot does not send the announced registries within the timeout
        """
        groups: list[PB_ParameterGroup] = await self._request(
            "get_parameter_groups", None, "parameter_groups", 0, timeout
        )

        self.registries = {}
        for group in groups:
            try:
                self.registries[group.name] = await self._discover_registry(group, timeout)
            except (TimeoutError, ValueError) as exc:
                logger.warning(f"Firmware parameter registry '{group.name}' left out: {exc}")

        self.parameters = {parameter.name: parameter for registry in self.registries.values() for parameter in registry}

    async def get_parameter_value(self, name: str, timeout: float = 1) -> float | int | bool:
        """
        Gets the value of a parameter from the firmware.

        Raises:
            KeyError: If the parameter has not been discovered
            TimeoutError: If no response is received within the timeout
        """
        parameter = self.parameters[name]

        response = await self._request(
            "get_parameter_value",
            parameter.model_dump(by_alias=True),
            "get_parameter_response",
            hash(parameter),
            timeout,
        )
        parameter.pb_read(response)

        return parameter.value

    async def set_parameter_value(self, name: str, value: float | int | bool, timeout: float = 1) -> None:
        """
        Sets the value of a parameter in the firmware.

        Raises:
            KeyError: If the parameter has not been discovered
            ValidationError: If the value does not match the parameter type or range
            FirmwareParameterValidationFailed: If the firmware rejects the value
            TimeoutError: If no response is received within the timeout
        """
        parameter = self.parameters[name]
        parameter.value = value

        response = await self._request(
            "set_parameter_value",
            parameter.model_dump(by_alias=True),
            "set_parameter_response",
            hash(parameter),
            timeout,
        )
        parameter.pb_read(response)

    async def reset_parameter_value(self, name: str, timeout: float = 1) -> None:
        """
        Resets a parameter to its default value in the firmware.

        Raises:
            KeyError: If the parameter has not been discovered
            FirmwareParameterValidationFailed: If the firmware rejects the reset
            TimeoutError: If no response is received within the timeout
        """
        parameter = self.parameters[name]

        response = await self._request(
            "reset_parameter_value",
            parameter.model_dump(by_alias=True),
            "reset_parameter_response",
            hash(parameter),
            timeout,
        )
        parameter.pb_read(response)

    async def _discover_registry(self, group: PB_ParameterGroup, timeout: float) -> list[FirmwareParameter]:
        """
        Lists the key hashes of a registry, in registry order, then gets the definition of each parameter.

        Registries are listed one at a time, since a list response does not tell its registry.

        Raises:
            TimeoutError: If a key hash or a definition is not received within the timeout
            ValueError: If the key hashes received do not match the registry hash
        """
        self.key_hashes = asyncio.Queue()

        try:
            await self.sio.emit("list_parameters", group.name, namespace=self.namespace)
            key_hashes = [await asyncio.wait_for(self.key_hashes.get(), timeout) for _ in range(group.count)]
        finally:
            self.key_hashes = None

        # The firmware hashes the little-endian key hashes, in registry order
        if fnv1a_hash_bytes(b"".join(key_hash.to_bytes(4, "little") for key_hash in key_hashes)) != group.registry_hash:
            raise ValueError("key hashes received do not match the registry hash")

        return list(
            await asyncio.gather(
                *(
                    self._request("get_parameter_definition", key_hash, "parameter_definition", key_hash, timeout)
                    for key_hash in key_hashes
                )
            )
        )

    async def _request(
        self,
        event: str,
        data: dict[str, Any] | int | None,
        response_event: str,
        key_hash: int,
        timeout: float,
    ) -> Any:
        """
        Sends a request and waits for its response, matched by response event and key hash.

        Raises:
            TimeoutError: If no response is received within the timeout
        """
        future = asyncio.get_running_loop().create_future()
        self.pending_requests[response_event, key_hash] = future

        try:
            await self.sio.emit(event, data, namespace=self.namespace)
            return await asyncio.wait_for(future, timeout)
        except TimeoutError:
            raise TimeoutError(f"No {response_event} received") from None
        finally:
            self.pending_requests.pop((response_event, key_hash), None)

    def resolve(self, response_event: str, key_hash: int, response: Any) -> None:
        """Resolves the Future of the request waiting for this response."""
        future = self.pending_requests.get((response_event, key_hash))

        if future and not future.done():
            future.set_result(response)

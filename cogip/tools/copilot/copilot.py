import asyncio
from asyncio.events import AbstractEventLoop
from pathlib import Path

from aioserial import AioSerial
from google.protobuf.json_format import MessageToDict as ProtobufMessageToDict
from google.protobuf.message import DecodeError as ProtobufDecodeError
from google.protobuf.message import Message as ProtobufMessage

from cogip import logger, models
from cogip.tools.copilot import queues
from .messages import PB_Menu, PB_State
from .message_types import InputMessageType, OutputMessageType


class Copilot():
    """
    Handle the connection to the serial port and async workers
    in charge sending, receiving and decoding messages from/to the robot (serial port)
    and from/to monitors (SocketIO/Web clients).

    This class is a singleton, to its constructor can be called from everywhere,
    it will always return the same unique object.
    """
    _instance = None                 # Unique instance of this class
    _port: Path = None               # Serial port
    _baud: int = None                # Serial baudrate
    _serial_port: AioSerial = None   # Async serial port
    _loop: AbstractEventLoop = None  # Event loop to use for all async objects
    _nb_connections: int = 0         # Number of monitors connected
    _menu: models.ShellMenu = None   # Last received shell menu

    def __new__(cls, *args, **kwargs):
        """
        Class constructor.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._serial_messages_received = asyncio.Queue()
            cls._pb_messages_to_send = asyncio.Queue()

        return cls._instance

    @property
    def port(self) -> Path:
        """Serial port"""
        return self._port

    @port.setter
    def port(self, new_port: Path):
        self._port = new_port

    @property
    def baud(self) -> int:
        """Serial baudrate"""
        return self._baud

    @baud.setter
    def baud(self, new_baud: int):
        self._baud = new_baud

    @property
    def nb_connections(self) -> int:
        """Number of monitors connected"""
        return self._nb_connections

    @nb_connections.setter
    def nb_connections(self, new_nb_connections: int):
        self._nb_connections = new_nb_connections

    def init_serial(self) -> None:
        """Initialize serial port."""
        if not self._loop:
            self._loop = asyncio.get_event_loop()

        self._serial_port = AioSerial(loop=self._loop)
        self._serial_port.port = str(self._port)
        self._serial_port.baudrate = self._baud
        self._serial_port.open()

    async def serial_receiver(self):
        """
        Async worker reading messages from the robot on serial ports.

        Messages encoding:

            - byte 1: message type
            - bytes 2-5: message length
            - bytes 6-*: Protobuf message

        Message length can be 0. In this case, only the message type matters.
        """
        while(True):
            message_type = int.from_bytes(await self._serial_port.readline_async(1), byteorder='little')
            message_length = int.from_bytes(await self._serial_port.readline_async(4), byteorder='little')
            encoded_message = b""
            if message_length:
                encoded_message = await self._serial_port.read_async(message_length)
            await queues.serial_messages_received.put((message_type, encoded_message))

    async def serial_sender(self):
        """
        Async worker encoding and sending Protobuf messages to the robot on serial ports.

        See `serial_receiver` for message encoding.
        """
        message_type: InputMessageType
        pb_message: ProtobufMessage

        while True:
            message_type, pb_message = await queues.serial_messages_to_send.get()
            message_type_byte = int.to_bytes(message_type, 1, byteorder='little', signed=False)
            await self._serial_port.write_async(message_type_byte)
            if pb_message:
                response_encoded = await self._loop.run_in_executor(None, pb_message.SerializeToString)
                length_bytes = int.to_bytes(len(response_encoded), 4, byteorder='little', signed=False)
                await self._serial_port.write_async(length_bytes)
                await self._serial_port.write_async(response_encoded)
            else:
                length_bytes = int.to_bytes(0, 4, byteorder='little', signed=False)
                await self._serial_port.write_async(length_bytes)

            queues.serial_messages_to_send.task_done()

    async def serial_decoder(self):
        """
        Async worker decoding messages received from the robot.
        """

        message_type: InputMessageType
        encoded_message: bytes
        request_handlers = {
            InputMessageType.MENU: (self.handle_message_menu, PB_Menu),
            InputMessageType.RESET: (self.handle_reset, None),
            InputMessageType.STATE: (self.handle_message_state, PB_State)
        }

        while True:
            message_type, encoded_message = await queues.serial_messages_received.get()
            request_handler, pb_message = request_handlers.get(message_type, (None, None))
            if not request_handler:
                logger.error(f"No handler found for message type '{message_type}'")
            elif not pb_message:
                await request_handler()
            else:
                try:
                    message = pb_message()
                    await self._loop.run_in_executor(None, message.ParseFromString, encoded_message)
                    await request_handler(message)
                except ProtobufDecodeError as exc:
                    logger.error(exc, encoded_message)

            queues.serial_messages_received.task_done()

    async def handle_reset(self) -> None:
        """
        Handle reset message. This means that the robot has just booted.

        Send a
        [MONITOR_CONNECTED][cogip.tools.copilot.message_types.OutputMessageType.MONITOR_CONNECTED]
        message to the robot on serial port for each connected monitor.

        Send a reset message to all connected monitors.
        """
        self._menu = None
        await queues.sio_messages_to_send.put(("reset", None))
        for _ in range(self._nb_connections):
            await queues.serial_messages_to_send.put((OutputMessageType.MONITOR_CONNECTED, None))

    async def handle_message_menu(self, menu: PB_Menu) -> None:
        """
        Send shell menu received from the robot to connected monitors.
        """
        menu_dict = ProtobufMessageToDict(menu)
        self._menu = models.ShellMenu.parse_obj(menu_dict)
        await self.emit_menu()

    async def handle_message_state(self, state: PB_State) -> None:
        """
        Send robot state received from the robot to connected monitors.
        """
        state_dict = ProtobufMessageToDict(
            state,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True
        )

        # Convert obstacles format to comply with Pydantic models used by the monitor
        obstacles = state_dict.get("obstacles", [])
        new_obstacles = [y for obstacle in obstacles for _, y in obstacle.items()]
        state_dict["obstacles"] = new_obstacles
        await queues.sio_messages_to_send.put(("state", state_dict))

    async def emit_menu(self) -> None:
        """
        Sent current shell menu to connected monitors.
        """
        if not self._menu or self._nb_connections == 0:
            return

        await queues.sio_messages_to_send.put(
            ("menu", self._menu.dict(exclude_defaults=True, exclude_unset=True))
        )

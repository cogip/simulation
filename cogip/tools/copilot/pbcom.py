import asyncio
import base64
import binascii
from pathlib import Path
from typing import Callable, Dict

from aioserial import AioSerial
from google.protobuf.message import DecodeError as ProtobufDecodeError

from . import logger


def pb_exception_handler(func):
    async def inner_function(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except ProtobufDecodeError as exc:
            logger.error(f"Protobuf decode error: {exc}")
        except Exception as exc:
            logger.error(f"{func}: Unknown Protobuf decode error in {type(exc)}: {exc}")
    return inner_function


class PBCom:
    _loop: asyncio.AbstractEventLoop = None          # Event loop to use for all async objects
    _serial_port: AioSerial = None                   # Async serial port
    _serial_messages_received: asyncio.Queue = None  # Queue for messages received from serial port
    _serial_messages_to_send: asyncio.Queue = None   # Queue for messages waiting to be sent on serial port

    def __init__(
            self,
            serial_port: Path,
            serial_baud: int,
            message_handlers: Dict[int, Callable]):

        self._serial_port = AioSerial()
        self._serial_port.port = str(serial_port)
        self._serial_port.baudrate = serial_baud
        self._message_handlers = message_handlers

        # Create asyncio queues
        self._serial_messages_received = asyncio.Queue()
        self._serial_messages_received = asyncio.Queue()
        self._serial_messages_to_send = asyncio.Queue()

        self._serial_port.open()

    async def run(self):
        """
        Start PBCom.
        """
        self._loop = asyncio.get_running_loop()

        await asyncio.gather(
            self.serial_decoder(),
            self.serial_receiver(),
            self.serial_sender()
        )

    async def serial_decoder(self):
        """
        Async worker decoding messages received from the robot.
        """
        uuid: int
        encoded_message: bytes

        while True:
            uuid, encoded_message = await self._serial_messages_received.get()
            request_handler = self._message_handlers.get(uuid)
            if not request_handler:
                print(f"No handler found for message uuid '{uuid}'")
            else:
                if not encoded_message:
                    await request_handler()
                else:
                    await request_handler(encoded_message)

            self._serial_messages_received.task_done()

    async def send_serial_message(self, *args) -> None:
        await self._serial_messages_to_send.put(args)

    async def serial_receiver(self):
        """
        Async worker reading messages from the robot on serial ports.

        Messages is base64-encoded and separated by `\\n`.
        After decoding, first byte is the message type, following bytes are
        the Protobuf encoded message (if any).
        """
        while(True):
            # Read next message
            message = await self._serial_port.readline_async()
            message = message.rstrip(b"\n")

            # Get message uuid on first bytes
            uuid = int.from_bytes(message[:4], "little")

            if len(message) == 4:
                await self._serial_messages_received.put((uuid, None))
                continue

            # Base64 decoding
            try:
                pb_message = base64.decodebytes(message[4:])
            except binascii.Error:
                print("Failed to decode base64 message.")
                continue

            # Send Protobuf message for decoding
            await self._serial_messages_received.put((uuid, pb_message))

    async def serial_sender(self):
        """
        Async worker encoding and sending Protobuf messages to the robot on serial ports.

        See `serial_receiver` for message encoding.
        """
        while True:
            uuid, pb_message = await self._serial_messages_to_send.get()
            await self._serial_port.write_async(uuid.to_bytes(4, "little"))
            if pb_message:
                response_serialized = await self._loop.run_in_executor(None, pb_message.SerializeToString)
                response_base64 = await self._loop.run_in_executor(None, base64.encodebytes, response_serialized)
                await self._serial_port.write_async(response_base64)
            await self._serial_port.write_async(b"\0")
            self._serial_messages_to_send.task_done()

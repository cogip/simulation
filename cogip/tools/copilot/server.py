import asyncio
import base64
import binascii
import json
import logging
from pathlib import Path
from typing import Any, Dict

from aioserial import AioSerial
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.protobuf.json_format import MessageToDict as ProtobufMessageToDict
from google.protobuf.message import DecodeError as ProtobufDecodeError
import socketio
from uvicorn.main import Server as UvicornServer

from cogip import models, logger
from cogip.tools.copilot.messages.PB_Samples_pb2 import PB_Samples
from .messages import PB_Menu, PB_Score, PB_State, PB_Wizard
from .recorder import GameRecordFileHandler
from .settings import Settings
from .sio_events import SioEvents


reset_uuid: int = 3351980141
command_uuid: int = 2168120333
menu_uuid: int = 1485239280
state_uuid: int = 3422642571
wizard_uuid: int = 1525532810
req_samples_uuid: int = 3781855956
resp_samples_uuid: int = 1538397045
copilot_connected_uuid: int = 1132911482
copilot_disconnected_uuid: int = 1412808668
score_uuid: int = 2552455996


def create_app() -> FastAPI:
    server = CopilotServer()
    return server.app


def pb_exception_handler(func):
    async def inner_function(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except ProtobufDecodeError as exc:
            logger.error(f"Protobuf decode error: {exc}")
        except Exception as exc:
            logger.error(f"Unknown Protobuf decode error {type(exc)}: {exc}")
    return inner_function


class CopilotServer:
    _serial_port: AioSerial = None                   # Async serial port
    _loop: asyncio.AbstractEventLoop = None          # Event loop to use for all async objects
    _nb_connections: int = 0                         # Number of monitors connected
    _menu: models.ShellMenu = None                   # Last received shell menu
    _samples: Dict[str, Any] = {}                    # Last detected samples
    _exiting: bool = False                           # True if Uvicorn server was ask to shutdown
    _record_handler: GameRecordFileHandler = None    # Log file handler to record games
    _serial_messages_received: asyncio.Queue = None  # Queue for messages received from serial port
    _serial_messages_to_send: asyncio.Queue = None   # Queue for messages waiting to be sent on serial port
    _original_uvicorn_exit_handler = UvicornServer.handle_exit  # Backup of original exit handler to overload it

    def __init__(self):
        """
        Class constructor.

        Create FastAPI application and SocketIO server.
        """
        self.settings = Settings()

        # Create FastAPI application
        self.app = FastAPI(title="COGIP Web Monitor", debug=False)
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False
        )
        self.sio.register_namespace(SioEvents(self))

        # Overload default Uvicorn exit handler
        UvicornServer.handle_exit = self.handle_exit

        # Create SocketIO server and mount it in /sio
        self.sio_app = socketio.ASGIApp(self.sio)
        self.app.mount("/sio", self.sio_app)

        # Mount static files
        current_dir = Path(__file__).parent
        self.app.mount("/static", StaticFiles(directory=current_dir/"static"), name="static")

        # Create HTML templates
        self.templates = Jinja2Templates(directory=current_dir/"templates")

        # Create game recorder
        self._game_recorder = logging.getLogger('GameRecorder')
        self._game_recorder.setLevel(logging.INFO)
        self._game_recorder.propagate = False
        try:
            self._record_handler = GameRecordFileHandler(self.settings.record_dir)
            self._game_recorder.addHandler(self._record_handler)
        except OSError:
            logger.warning(f"Failed to record games in directory '{self.settings.record_dir}'")
            self._record_handler = None

        # Open serial port
        self._serial_port = AioSerial()
        self._serial_port.port = str(self.settings.serial_port)
        self._serial_port.baudrate = self.settings.serial_baud
        self._serial_port.open()

        self.register_endpoints()

    def sio_client_connected(self) -> None:
        """Add one connected client"""
        self._nb_connections += 1

    def sio_client_disconnected(self) -> None:
        """Remove one connected client"""
        self._nb_connections -= 1

    def set_samples(self, samples: Dict[str, Any]) -> None:
        self._samples = samples

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        CopilotServer._exiting = True
        CopilotServer._original_uvicorn_exit_handler(*args, **kwargs)

    async def send_serial_message(self, *args) -> None:
        await self._serial_messages_to_send.put(args)

    async def serial_receiver(self):
        """
        Async worker reading messages from the robot on serial ports.

        Messages is base64-encoded and separated by '\n'.
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

    async def serial_decoder(self):
        """
        Async worker decoding messages received from the robot.
        """
        encoded_message: bytes
        request_handlers = {
            reset_uuid: self.handle_reset,
            menu_uuid: self.handle_message_menu,
            state_uuid: self.handle_message_state,
            wizard_uuid: self.handle_message_wizard,
            req_samples_uuid: self.handle_samples_request,
            score_uuid: self.handle_score
        }

        while True:
            uuid, encoded_message = await self._serial_messages_received.get()
            request_handler = request_handlers.get(uuid)
            if not request_handler:
                print(f"No handler found for message uuid '{uuid}'")
            else:
                if not encoded_message:
                    await request_handler()
                else:
                    await request_handler(encoded_message)

            self._serial_messages_received.task_done()

    async def handle_reset(self) -> None:
        """
        Handle reset message. This means that the robot has just booted.

        Send a reset message to all connected monitors.
        """
        self._menu = None
        await self.send_serial_message(copilot_connected_uuid, None)
        await self.sio.emit("reset")
        if self._record_handler:
            await self._loop.run_in_executor(None, self._record_handler.doRollover)

    @pb_exception_handler
    async def handle_message_menu(self, message: bytes) -> None:
        """
        Send shell menu received from the robot to connected monitors.
        """
        pb_menu = PB_Menu()
        await self._loop.run_in_executor(None, pb_menu.ParseFromString, message)

        menu = ProtobufMessageToDict(pb_menu)
        self._menu = models.ShellMenu.parse_obj(menu)
        await self.emit_menu()

    @pb_exception_handler
    async def handle_message_state(self, message: bytes) -> None:
        """
        Send robot state received from the robot to connected monitors.
        """
        pb_state = PB_State()
        await self._loop.run_in_executor(None, pb_state.ParseFromString, message)

        state = ProtobufMessageToDict(
            pb_state,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True
        )

        # Convert obstacles format to comply with Pydantic models used by the monitor
        obstacles = state.get("obstacles", [])
        new_obstacles = []
        for obstacle in obstacles:
            bb = obstacle.pop("bounding_box")
            try:
                new_obstacle = list(obstacle.values())[0]
            except IndexError:
                continue
            new_obstacle["bb"] = bb
            new_obstacles.append(new_obstacle)
        state["obstacles"] = new_obstacles
        await self.sio.emit("state", state)
        await self._loop.run_in_executor(None, self.record_state, state)

    @pb_exception_handler
    async def handle_message_wizard(self, message: bytes) -> None:
        pb_wizard = PB_Wizard()
        await self._loop.run_in_executor(None, pb_wizard.ParseFromString, message)

        wizard = ProtobufMessageToDict(
            pb_wizard,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True
        )
        wizard_type = pb_wizard.WhichOneof("type")
        wizard["type"] = wizard_type
        wizard.update(**wizard[wizard_type])
        del wizard[wizard_type]
        await self.sio.emit("wizard", wizard)

    async def handle_samples_request(self) -> None:
        pb_samples = PB_Samples()
        for (id, coords) in sorted(self._samples.items()):
            pb_samples.samples.add(
                tag=int(id),
                x=coords[0],
                y=coords[1],
                z=coords[2],
                rot_x=coords[3],
                rot_y=coords[4],
                rot_z=coords[5]
            )
            pb_samples.has_samples = True
        await self.send_serial_message(resp_samples_uuid, pb_samples)

    @pb_exception_handler
    async def handle_score(self, message: bytes) -> None:
        """
        Send shell menu received from the robot to connected monitors.
        """
        pb_score = PB_Score()
        await self._loop.run_in_executor(None, pb_score.ParseFromString, message)

        score = ProtobufMessageToDict(pb_score)
        await self.sio.emit("score", score.value)

    async def emit_menu(self) -> None:
        """
        Sent current shell menu to connected monitors.
        """
        if not self._menu or self._nb_connections == 0:
            return

        await self.sio.emit(
            "menu",
            self._menu.dict(exclude_defaults=True, exclude_unset=True)
        )

    def record_state(self, state: Dict[str, Any]) -> None:
        """
        Add a robot robot state in the current record file.
        Do it only the the robot the game has started, ie mode != 0.
        """
        if self._record_handler and state.get("mode", 0):
            self._game_recorder.info(json.dumps(state))

    def register_endpoints(self) -> None:

        @self.app.on_event("startup")
        async def startup_event():
            """
            Function called at FastAPI server startup.

            Initialize serial port, message queues and start async workers.
            Also send a
            [COPILOT_CONNECTED][cogip.tools.copilot.message_types.OutputMessageType.COPILOT_CONNECTED]
            message on serial port.
            """
            self._loop = asyncio.get_event_loop()

            # Create asyncio queues
            self._serial_messages_received = asyncio.Queue()
            self._serial_messages_received = asyncio.Queue()
            self._serial_messages_to_send = asyncio.Queue()

            # Create async workers
            asyncio.create_task(self.serial_decoder(), name="Serial Decoder")
            asyncio.create_task(self.serial_receiver(), name="Serial Receiver")
            asyncio.create_task(self.serial_sender(), name="Serial Sender")

            # Send CONNECTED message to firmware
            await self.send_serial_message(copilot_connected_uuid, None)

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """
            Function called at FastAPI server shutdown.

            Send a
            [COPILOT_DISCONNECTED][cogip.tools.copilot.message_types.OutputMessageType.COPILOT_DISCONNECTED]
            message on serial port.
            Wait for all serial messages to be sent.
            """
            await self.send_serial_message(copilot_disconnected_uuid, None)
            await self._serial_messages_to_send.join()

        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """
            Homepage of the dashboard web server.
            """
            return self.templates.TemplateResponse("index.html", {"request": request})

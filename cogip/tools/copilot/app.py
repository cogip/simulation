import asyncio
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import socketio

from cogip.tools.copilot import queues
from .copilot import Copilot
from .messages import PB_Command
from .message_types import OutputMessageType

current_dir = Path(__file__).parent

app = FastAPI(title="COGIP Web Monitor", debug=False)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)
sio_app = socketio.ASGIApp(sio)
app.mount("/sio", sio_app)
app.mount("/static", StaticFiles(directory=current_dir/"static"), name="static")
templates = Jinja2Templates(directory=current_dir/"templates")


async def sio_sender():
    """
    Async worker waiting for messages to send to monitors through SocketIO server.
    """
    message_type: str
    message_dict: Dict

    while True:
        message_type, message_dict = await queues.sio_messages_to_send.get()
        await sio.emit(message_type, message_dict)
        queues.sio_messages_to_send.task_done()


@app.on_event("startup")
async def startup_event():
    """
    Function called at FastAPI server startup.

    Initialize serial port, message queues and start async workers.
    Also send a
    [COPILOT_CONNECTED][cogip.tools.copilot.message_types.OutputMessageType.COPILOT_CONNECTED]
    message on serial port.
    """
    copilot = Copilot()
    copilot.init_serial()

    loop = asyncio.get_event_loop()
    queues.serial_messages_received = asyncio.Queue(loop=loop)
    queues.serial_messages_to_send = asyncio.Queue(loop=loop)
    queues.sio_messages_to_send = asyncio.Queue(loop=loop)

    asyncio.create_task(copilot.serial_decoder(), name="Serial Decoder")
    asyncio.create_task(copilot.serial_receiver(), name="Serial Receiver")
    asyncio.create_task(copilot.serial_sender(), name="Serial Sender")
    asyncio.create_task(sio_sender(), name="SocketIO Sender")

    await queues.serial_messages_to_send.put((OutputMessageType.COPILOT_CONNECTED, None))


@app.on_event("shutdown")
async def shutdown_event():
    """
    Function called at FastAPI server shutdown.

    Send a
    [COPILOT_DISCONNECTED][cogip.tools.copilot.message_types.OutputMessageType.COPILOT_DISCONNECTED]
    message on serial port.
    Wait for all serial messages to be sent.
    """
    await queues.serial_messages_to_send.put((OutputMessageType.COPILOT_DISCONNECTED, None))
    await queues.serial_messages_to_send.join()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Homepage of the dashboard web server.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@sio.event
async def connect(sid, environ):
    """
    Callback on new monitor connection.

    Send a
    [MONITOR_CONNECTED][cogip.tools.copilot.message_types.OutputMessageType.MONITOR_CONNECTED]
    message on serial port.
    Send the current menu to monitors.
    """
    copilot = Copilot()
    copilot.nb_connections += 1
    await queues.serial_messages_to_send.put((OutputMessageType.MONITOR_CONNECTED, None))
    await copilot.emit_menu()


@sio.event
async def disconnect(sid):
    """
    Callback on monitor disconnection.

    Send a
    [MONITOR_DISCONNECTED][cogip.tools.copilot.message_types.OutputMessageType.MONITOR_DISCONNECTED]
    message on serial port.
    """
    copilot = Copilot()
    copilot.nb_connections -= 1
    await queues.serial_messages_to_send.put((OutputMessageType.MONITOR_DISCONNECTED, None))


@sio.on("break")
async def on_break(sid):
    """
    Callback on break message.

    Send a
    [BREAK][cogip.tools.copilot.message_types.OutputMessageType.BREAK]
    message on serial port: if the robot is booting, it will abort
    automatic start of the planner.
    """
    await queues.serial_messages_to_send.put((OutputMessageType.BREAK, None))


@sio.on("cmd")
async def on_cmd(sid, data):
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
    await queues.serial_messages_to_send.put((OutputMessageType.COMMAND, response))

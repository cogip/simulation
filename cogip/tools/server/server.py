from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import socketio
from socketio.exceptions import ConnectionRefusedError
from uvicorn.main import Server as UvicornServer

from . import logger, namespaces, routes


def create_app() -> FastAPI:
    server = Server()
    return server.app


class Server:
    _exiting: bool = False                           # True if Uvicorn server was ask to shutdown
    _original_uvicorn_exit_handler = UvicornServer.handle_exit  # Backup of original exit handler to overload it

    def __init__(self):
        """
        Class constructor.

        Create FastAPI application and SocketIO server.
        """
        # Create FastAPI application
        self.app = FastAPI(title="COGIP Web Monitor", debug=False)
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False
        )
        self.sio.register_namespace(namespaces.DashboardNamespace())
        self.sio.register_namespace(namespaces.MonitorNamespace())
        self.sio.register_namespace(namespaces.CopilotNamespace())
        self.sio.register_namespace(namespaces.DetectorNamespace())
        self.sio.register_namespace(namespaces.PlannerNamespace())
        self.sio.register_namespace(namespaces.RobotcamNamespace())

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

        # Register routes
        self.app.include_router(routes.RootRouter(self.templates), prefix="")

        @self.sio.event
        def connect(sid, environ, auth):
            logger.warning(f"A client tried to connect to namespace / (sid={sid})")
            raise ConnectionRefusedError("Connection refused to namespace /")

        @self.sio.on("*")
        def catch_all(event, sid, data):
            logger.warning(f"A client tried to send data to namespace / (sid={sid}, event={event})")

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        Server._exiting = True
        Server._original_uvicorn_exit_handler(*args, **kwargs)

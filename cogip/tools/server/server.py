from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
import socketio
from socketio.exceptions import ConnectionRefusedError
from uvicorn.main import Server as UvicornServer

from cogip import models
from . import context, logger, namespaces, routes


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
            always_connect=False,
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False
        )
        self.sio.register_namespace(namespaces.DashboardNamespace())
        self.sio.register_namespace(namespaces.MonitorNamespace())
        self.sio.register_namespace(namespaces.CopilotNamespace(self))
        self.sio.register_namespace(namespaces.DetectorNamespace(self))
        self.sio.register_namespace(namespaces.PlannerNamespace(self))
        self.sio.register_namespace(namespaces.RobotcamNamespace())

        # Overload default Uvicorn exit handler
        UvicornServer.handle_exit = self.handle_exit

        self._context = context.Context()
        self._root_menu = models.ShellMenu(name="Root Menu", entries=[])
        self._context.tool_menus["root"] = self._root_menu
        self._context.current_tool_menu = "root"

        # Create SocketIO server and mount it in /sio
        self.sio_app = socketio.ASGIApp(self.sio)
        self.app.mount("/sio", self.sio_app)

        # Mount static files
        current_dir = Path(__file__).parent
        self.app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

        # Create HTML templates
        self.templates = Jinja2Templates(directory=current_dir / "templates")

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

    async def register_menu(self, namespace: str, data: Dict[str, Any]) -> None:
        name = data.get("name")
        if not name:
            logger.warning(f"register_menu: missing 'name' in data: {data}")
            return
        menu_dict = data.get("menu")
        if not menu_dict:
            logger.warning(f"register_menu: missing 'menu' in data: {data}")
            return
        try:
            menu = models.ShellMenu.parse_obj(menu_dict)
        except ValidationError as exc:
            logger.warning(f"register_menu: cannot validate 'menu': {exc}")
            return

        ns_name = f"{namespace}/{name}"
        entry = models.MenuEntry(cmd=ns_name, desc=f"{menu.name} Menu")
        if ns_name not in self._context.tool_menus:
            self._root_menu.entries.append(entry)
        exit_entry = models.MenuEntry(cmd="exit", desc="Exit Menu")
        menu.entries.append(exit_entry)
        self._context.tool_menus[ns_name] = menu
        await self.sio.emit(
            "tool_menu",
            self._context.tool_menus[self._context.current_tool_menu].dict(),
            namespace="/dashboard"
        )

    async def unregister_menu(self, name: str) -> None:
        pass

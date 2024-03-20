import asyncio
import os

import socketio
from socketio.exceptions import ConnectionRefusedError
from uvicorn.main import Server as UvicornServer

from . import logger, namespaces
from .robot import Robot


class Server:
    original_uvicorn_exit_handler = UvicornServer.handle_exit
    exiting: bool = False
    robots: dict[int, Robot] = {}
    robot_tasks: set[asyncio.Task] = set()

    def __init__(self):
        """
        Class constructor.

        Create SocketIO server and robot servers connections
        """
        UvicornServer.handle_exit = Server.handle_exit

        self.sio = socketio.AsyncServer(
            always_connect=False,
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
        )
        self.app = socketio.ASGIApp(self.sio)
        self.sio.register_namespace(namespaces.DashboardNamespace(self))

        for i in range(1, int(os.environ["SERVER_BEACON_MAX_ROBOTS"]) + 1):
            robot = Robot(self, i)
            task = asyncio.create_task(robot.run())
            Server.robots[i] = robot
            Server.robot_tasks.add(task)
            task.add_done_callback(Server.robot_tasks.discard)

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
        Server.exiting = True
        for _, robot in Server.robots.items():
            robot.exiting = True
            robot.sio.reconnection_attempts = -1
        for task in Server.robot_tasks:
            task.cancel()

        Server.original_uvicorn_exit_handler(*args, **kwargs)

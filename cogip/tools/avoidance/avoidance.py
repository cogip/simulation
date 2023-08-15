import asyncio
import time
from typing import Any

import socketio

from . import sio_events
from .properties import Properties


class Avoidance:
    """
    Main avoidance class.
    """

    def __init__(
            self,
            server_url: str,
            id: int,
            robot_width: int,
            obstacle_radius: int,
            obstacle_bb_margin: float,
            obstacle_bb_vertices: int,
            max_distance: int,
            obstacle_sender_interval: float,
            path_refresh_interval: float,
            plot: bool,
            debug: bool):
        """
        Class constructor.

        Arguments:
            server_url: Server URL
            id: robot id
            robot_width: Width of the robot (in )
            obstacle_radius: Radius of a dynamic obstacle (in mm)
            obstacle_bb_margin: Obstacle bounding box margin in percent of the radius
            obstacle_bb_vertices: Number of obstacle bounding box vertices
            max_distance: Maximum distance to take avoidance points into account (mm)
            obstacle_sender_interval: Interval between each send of obstacles to dashboards (in seconds)
            path_refresh_interval: Interval between each update of robot paths (in seconds)
            plot: Display avoidance graph in realtime
            debug: enable debug messages
        """
        self._server_url = server_url
        self._id = id
        self._debug = debug
        self._properties = Properties(
            robot_width=robot_width,
            obstacle_radius=obstacle_radius,
            obstacle_bb_margin=obstacle_bb_margin,
            obstacle_bb_vertices=obstacle_bb_vertices,
            max_distance=max_distance,
            obstacle_sender_interval=obstacle_sender_interval,
            path_refresh_interval=path_refresh_interval,
            plot=plot
        )
        self._retry_connection = True
        self._sio = socketio.AsyncClient(logger=False)
        self._sio_ns = sio_events.SioEvents(self)
        self._sio.register_namespace(self._sio_ns)

    async def run(self):
        """
        Start copilot.
        """
        # self._loop = asyncio.get_running_loop()

        self.retry_connection = True
        await self.try_connect()
        while True:
            await asyncio.sleep(1)

    async def try_connect(self):
        """
        Poll to wait for the first connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while self.retry_connection:
            try:
                await self._sio.connect(
                    self._server_url,
                    socketio_path="sio/socket.io",
                    namespaces=["/avoidance"],
                    auth={"id": self._id}
                )
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    @property
    def try_reconnection(self) -> bool:
        """
        Return true if Avoidance should continue to try to connect to the server,
        false otherwise.
        """
        return self._retry_connection

    @try_reconnection.setter
    def try_reconnection(self, new_value: bool) -> None:
        self._retry_connection = new_value

    @property
    def id(self) -> int:
        return self._id

    def update_config(self, config: dict[str, Any]) -> None:
        """
        Update an Avoidance property with the value sent by the dashboard.
        """
        self._properties.__setattr__(config["name"], config["value"])

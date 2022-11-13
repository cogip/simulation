from threading import Thread
import time
from typing import Dict, List, Optional

from pydantic import parse_obj_as
from PySide6 import QtCore
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot
import socketio

from cogip.models import models


class SocketioController(QtCore.QObject):
    """
    This class controls the socket.io port used to communicate with the server.
    Its main purpose is to get the shell and tool menus to update the interface,
    get the robot position to update its position, and send the commands
    to the robot and to the tools.

    Attributes:
        signal_new_console_text:
            Qt signal emitted to log messages in UI console
        signal_new_menu:
            Qt signal emitted to load a new shell/tool menu
        signal_new_robot_pose_current:
            Qt signal emitted on robot pose current update
        signal_new_robot_pose_order:
            Qt signal emitted on robot pose order update
        signal_new_robot_state:
            Qt signal emitted on robot state update
        signal_new_dyn_obstacles:
            Qt signal emitted on dynamic obstacles update
        signal_connected:
            Qt signal emitted on server connection state changes
        signal_exit:
            Qt signal emitted to exit Monitor
        signal_start_lidar_emulation:
            Qt signal emitted to start Lidar emulation
        signal_stop_lidar_emulation:
            Qt signal emitted to stop Lidar emulation
        last_cycle:
            Record the last cycle to avoid sending the same data several times
    """
    signal_new_console_text: qtSignal = qtSignal(str)
    signal_new_menu: qtSignal = qtSignal(str, models.ShellMenu)
    signal_new_robot_pose_current: qtSignal = qtSignal(models.Pose)
    signal_new_robot_pose_order: qtSignal = qtSignal(models.Pose)
    signal_new_robot_state: qtSignal = qtSignal(models.RobotState)
    signal_new_dyn_obstacles: qtSignal = qtSignal(list)
    signal_connected: qtSignal = qtSignal(bool)
    signal_exit: qtSignal = qtSignal()
    signal_start_lidar_emulation: qtSignal = qtSignal()
    signal_stop_lidar_emulation: qtSignal = qtSignal()
    last_cycle: int = 0

    def __init__(self, url: str):
        """
        Class constructor.

        Arguments:
            url: URL to socket.io server
        """
        super().__init__()

        self.url = url
        self.sio = socketio.Client()
        self.register_handlers()

        self.menus: Dict[str, Optional[models.ShellMenu]] = {
            "shell": None,
            "tool": None
        }

    def start(self):
        """
        Connect to socket.io server.
        """
        # Poll in background to wait for the first connection.
        # Deconnections/reconnections are handle directly by the client.
        self._retry_connection = True
        Thread(target=self.try_connect).start()

    def try_connect(self):
        while(self._retry_connection):
            try:
                self.sio.connect(self.url, socketio_path="sio/socket.io", namespaces=["/monitor", "/dashboard"])
            except socketio.exceptions.ConnectionError as ex:
                print(ex)
                time.sleep(2)
                continue
            break

    def stop(self):
        """
        Disconnect from socket.io server.
        """
        self._retry_connection = False
        if self.sio.connected:
            self.sio.disconnect()

    @qtSlot(str)
    def new_command(self, menu_name: str, command: str):
        """
        Send a command to the robot.

        Arguments:
            menu_name: menu to update ("shell", "tool", ...)
            command: Command to send
        """
        self.signal_new_console_text.emit(f"Send '{command}' to {menu_name}")
        self.sio.emit(menu_name + "_cmd", command, namespace="/dashboard")

    def on_menu(self, menu_name: str, data):
        menu = models.ShellMenu.parse_obj(data)
        if self.menus[menu_name] != menu:
            self.menus[menu_name] = menu
            self.signal_new_menu.emit(menu_name, menu)

    def register_handlers(self):
        """
        Define socket.io message handlers.
        """

        @self.sio.event(namespace="/monitor")
        def connect():
            """
            Callback on server connection.
            """
            self.signal_new_console_text.emit("Connected to server")
            self.signal_connected.emit(True)

        @self.sio.event(namespace="/monitor")
        def connect_error(data):
            """
            Callback on server connection error.
            """
            if (
                data and
                isinstance(data, dict) and
                (message := data.get("message")) and
                message == "A monitor is already connected"
               ):
                print(f"Error: {message}.")
                self._retry_connection = False
                self.signal_exit.emit()
                return
            print("Connection error:", data)
            self.signal_new_console_text.emit("Connection to server failed.")
            self.signal_connected.emit(False)

        @self.sio.event(namespace="/monitor")
        def disconnect():
            """
            Callback on server disconnection.
            """
            self.signal_new_console_text.emit("Disconnected from server.")
            self.signal_connected.emit(False)

        @self.sio.on("shell_menu", namespace="/dashboard")
        def on_shell_menu(data):
            """
            Callback on shell menu message.
            """
            self.on_menu("shell", data)

        @self.sio.on("tool_menu", namespace="/dashboard")
        def on_tool_menu(data):
            """
            Callback on tool menu message.
            """
            self.on_menu("tool", data)

        @self.sio.on("pose_current", namespace="/dashboard")
        def on_pose_current(data):
            """
            Callback on robot pose current message.
            """
            pose = models.Pose.parse_obj(data)
            self.signal_new_robot_pose_current.emit(pose)

        @self.sio.on("pose_order", namespace="/dashboard")
        def on_pose_order(data):
            """
            Callback on robot pose order message.
            """
            pose = models.Pose.parse_obj(data)
            self.signal_new_robot_pose_order.emit(pose)

        @self.sio.on("state", namespace="/dashboard")
        def on_state(data):
            """
            Callback on robot state message.
            """
            state = models.RobotState.parse_obj(data)
            if state.cycle != self.last_cycle:
                self.last_cycle = state.cycle
                self.signal_new_robot_state.emit(state)

        @self.sio.on("obstacles", namespace="/dashboard")
        def on_obstacles(data):
            """
            Callback on obstacles message.
            """
            obstacles = parse_obj_as(models.DynObstacleList, data)
            self.signal_new_dyn_obstacles.emit(obstacles)

        @self.sio.on("start_lidar_emulation", namespace="/monitor")
        def on_start_lidar_emulation():
            """
            Start Lidar emulation.
            """
            self.signal_start_lidar_emulation.emit()

        @self.sio.on("stop_lidar_emulation", namespace="/monitor")
        def on_stop_lidar_emulation():
            """
            Stop Lidar emulation.
            """
            self.signal_stop_lidar_emulation.emit()

    def emit_lidar_data(self, data: List[int]) -> None:
        """
        Send Lidar data to server.

        Arguments:
            data: List of distances for each angle
        """
        if self.sio.connected:
            self.sio.emit("lidar_data", data, namespace="/monitor")

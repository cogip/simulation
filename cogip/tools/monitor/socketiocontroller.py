from threading import Thread
import time
from typing import Any, Dict, List, Optional

import polling2
from pydantic import parse_obj_as
from PySide6 import QtCore
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot
import socketio

from cogip.models import models
from cogip.models.actuators import ActuatorCommand, ActuatorsState


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
        signal_new_robot_path:
            Qt signal emitted on robot path update
        signal_new_dyn_obstacles:
            Qt signal emitted on dynamic obstacles update
        signal_connected:
            Qt signal emitted on server connection state changes
        signal_exit:
            Qt signal emitted to exit Monitor
        signal_add_robot:
            Qt signal emitted to add a new robot
        signal_del_robot:
            Qt signal emitted to remove a robot
        signal_wizard_request:
            Qt signal emitted to forward wizard requests
        signal_start_lidar_emulation:
            Qt signal emitted to start Lidar emulation
        signal_stop_lidar_emulation:
            Qt signal emitted to stop Lidar emulation
        signal_config_request:
            Qt signal emitted to load a new shell/tool menu
    """
    signal_new_console_text: qtSignal = qtSignal(str)
    signal_new_menu: qtSignal = qtSignal(str, models.ShellMenu)
    signal_new_robot_pose_current: qtSignal = qtSignal(int, models.Pose)
    signal_new_robot_pose_order: qtSignal = qtSignal(int, models.Pose)
    signal_new_robot_state: qtSignal = qtSignal(int, models.RobotState)
    signal_new_robot_path: qtSignal = qtSignal(int, list)
    signal_new_dyn_obstacles: qtSignal = qtSignal(list)
    signal_connected: qtSignal = qtSignal(bool)
    signal_exit: qtSignal = qtSignal()
    signal_add_robot: qtSignal = qtSignal(int)
    signal_del_robot: qtSignal = qtSignal(int)
    signal_wizard_request: qtSignal = qtSignal(dict)
    signal_close_wizard: qtSignal = qtSignal()
    signal_start_lidar_emulation: qtSignal = qtSignal(int)
    signal_stop_lidar_emulation: qtSignal = qtSignal(int)
    signal_config_request: qtSignal = qtSignal(dict)
    signal_actuators_state: qtSignal = qtSignal(ActuatorsState)

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

        self.menus: Dict[str, Optional[models.ShellMenu]] = {}

    def start(self):
        """
        Connect to socket.io server.
        """
        # Poll in background to wait for the first connection.
        # Deconnections/reconnections are handle directly by the client.
        self._retry_connection = True
        Thread(target=self.try_connect).start()

    def try_connect(self):
        while self._retry_connection:
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
        name, _, robot_id = menu_name.partition(" ")
        if name == "shell":
            self.sio.emit("shell_cmd", (int(robot_id), command), namespace="/dashboard")
        else:
            self.sio.emit(f"{menu_name}_cmd", command, namespace="/dashboard")
        self.signal_new_console_text.emit(f"Send '{command}' to {menu_name}")

    @qtSlot(dict)
    def config_updated(self, config: Dict[str, Any]):
        self.sio.emit("config_updated", config, namespace="/dashboard")

    @qtSlot(dict)
    def wizard_response(self, response: dict[str, Any]):
        self.sio.emit("wizard", response, namespace="/dashboard")

    def new_actuator_command(self, robot_id: int, command: ActuatorCommand):
        """
        Send an actuator command to the robot.

        Arguments:
            robot_id: related robot id
            command: actuator command to send
        """
        self.sio.emit(
            "actuator_command",
            data={
                "robot_id": robot_id,
                "command": command.dict()
            },
            namespace="/dashboard"
        )

    def actuators_closed(self, robot_id: str):
        """
        Request to stop emitting actuators state from the robot.

        Arguments:
            robot_id: related robot id
        """
        self.sio.emit("actuators_stop", data=robot_id, namespace="/dashboard")

    def on_menu(self, menu_name: str, data):
        menu = models.ShellMenu.parse_obj(data)
        if self.menus.get(menu_name) != menu:
            self.menus[menu_name] = menu
            self.signal_new_menu.emit(menu_name, menu)

    def register_handlers(self):
        """
        Define socket.io message handlers.
        """

        @self.sio.on("connect", namespace="/dashboard")
        def dashboard_connect():
            """
            Callback on server connection.
            """
            polling2.poll(lambda: self.sio.connected is True, step=0.2, poll_forever=True)
            self.sio.emit("connected", namespace="/dashboard")

        @self.sio.on("monitor", namespace="/monitor")
        def monitor_connect():
            """
            Callback on server connection.
            """
            polling2.poll(
                lambda: self.sio.connected is True,
                step=1,
                poll_forever=True
            )
            self.sio.emit("connected", namespace="/monitor")
            self.signal_new_console_text.emit("Connected to server")
            self.signal_connected.emit(True)

        @self.sio.event(namespace="/monitor")
        def connect_error(data):
            """
            Callback on server connection error.
            """
            if data \
               and isinstance(data, dict) \
               and (message := data.get("message")) \
               and message == "A monitor is already connected":
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
        def on_shell_menu(robot_id: int, menu: Dict[str, Any]) -> None:
            """
            Callback on shell menu message.
            """
            self.on_menu(f"shell {robot_id}", menu)

        @self.sio.on("tool_menu", namespace="/dashboard")
        def on_tool_menu(data):
            """
            Callback on tool menu message.
            """
            self.on_menu("tool", data)

        @self.sio.on("config", namespace="/dashboard")
        def on_config(config):
            """
            Callback on config request.
            """
            self.signal_config_request.emit(config)

        @self.sio.on("actuators_state", namespace="/dashboard")
        def on_actuators_state(actuators_state):
            """
            Callback on actuators_state message.
            """
            state = ActuatorsState.parse_obj(actuators_state)
            self.signal_actuators_state.emit(state)

        @self.sio.on("pose_current", namespace="/dashboard")
        def on_pose_current(robot_id: int, data: Dict[str, Any]) -> None:
            """
            Callback on robot pose current message.
            """
            pose = models.Pose.parse_obj(data)
            self.signal_new_robot_pose_current.emit(robot_id, pose)

        @self.sio.on("pose_order", namespace="/dashboard")
        def on_pose_order(robot_id: int, data: Dict[str, Any]) -> None:
            """
            Callback on robot pose order message.
            """
            pose = models.Pose.parse_obj(data)
            self.signal_new_robot_pose_order.emit(robot_id, pose)

        @self.sio.on("state", namespace="/dashboard")
        def on_state(robot_id: int, data: Dict[str, Any]) -> None:
            """
            Callback on robot state message.
            """
            state = models.RobotState.parse_obj(data)
            self.signal_new_robot_state.emit(robot_id, state)

        @self.sio.on("path", namespace="/dashboard")
        def on_path(robot_id: int, data: list[dict[str, float]]) -> None:
            """
            Callback on robot path message.
            """
            path = parse_obj_as(list[models.Vertex], data)
            self.signal_new_robot_path.emit(robot_id, path)

        @self.sio.on("obstacles", namespace="/dashboard")
        def on_obstacles(data):
            """
            Callback on obstacles message.
            """
            obstacles = parse_obj_as(models.DynObstacleList, data)
            self.signal_new_dyn_obstacles.emit(obstacles)

        @self.sio.on("add_robot", namespace="/dashboard")
        def on_add_robot(robot_id: int) -> None:
            """
            Add a new robot.
            """
            self.signal_add_robot.emit(robot_id)

        @self.sio.on("del_robot", namespace="/dashboard")
        def on_del_robot(robot_id: int) -> None:
            """
            Remove a robot.
            """
            self.signal_del_robot.emit(robot_id)

        @self.sio.on("wizard", namespace="/dashboard")
        def on_wizard_request(data: Dict[str, Any]) -> None:
            """
            Wizard request.
            """
            self.signal_wizard_request.emit(data)

        @self.sio.on("close_wizard", namespace="/dashboard")
        def on_close_wizard() -> None:
            """
            Close wizard.
            """
            self.signal_close_wizard.emit()

        @self.sio.on("start_lidar_emulation", namespace="/monitor")
        def on_start_lidar_emulation(robot_id: int) -> None:
            """
            Start Lidar emulation.
            """
            self.signal_start_lidar_emulation.emit(robot_id)

        @self.sio.on("stop_lidar_emulation", namespace="/monitor")
        def on_stop_lidar_emulation(robot_id: int) -> None:
            """
            Stop Lidar emulation.
            """
            self.signal_stop_lidar_emulation.emit(robot_id)

    def emit_lidar_data(self, robot_id: int, data: List[int]) -> None:
        """
        Send Lidar data to server.

        Arguments:
            robot_id: ID of the robot
            data: List of distances for each angle
        """
        if self.sio.connected:
            self.sio.emit("lidar_data", (robot_id, data), namespace="/monitor")

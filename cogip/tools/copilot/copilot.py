import asyncio
import copy
from pathlib import Path
import time

from google.protobuf.json_format import MessageToDict
import socketio

from cogip import models
from .messages import PB_ActuatorsState, PB_Menu, PB_Pids, PB_Pose, PB_State
from .pbcom import PBCom, pb_exception_handler
from .pid import Pid, Pids
from .sio_events import SioEvents


reset_uuid: int = 3351980141
command_uuid: int = 2168120333
menu_uuid: int = 1485239280
state_uuid: int = 3422642571
copilot_connected_uuid: int = 1132911482
copilot_disconnected_uuid: int = 1412808668
pose_order_uuid: int = 1534060156
pose_reached_uuid: int = 2736246403
pose_start_uuid: int = 2741980922
actuators_thread_start_uuid: int = 1525532810
actuators_thread_stop_uuid: int = 3781855956
actuators_state_uuid: int = 1538397045
actuators_command_uuid: int = 2552455996
pid_request_uuid: int = 3438831927
pid_uuid: int = 4159164681
controller_uuid: int = 2750239003
game_start_uuid: int = 3138845474
game_end_uuid: int = 1532296089
game_reset_uuid: int = 1549868731
brake_uuid: int = 3239255374


class Copilot:
    """
    Main copilot class.
    """
    _loop: asyncio.AbstractEventLoop = None          # Event loop to use for all coroutines

    def __init__(
            self,
            server_url: str,
            id: int,
            serial_port: Path,
            serial_baud: int):
        """
        Class constructor.

        Arguments:
            server_url: server URL
            id: robot id
            serial_port: serial port connected to STM32 device
            serial_baud: baud rate
        """
        self._server_url = server_url
        self._id = id
        self._retry_connection = True
        self._shell_menu: models.ShellMenu | None = None
        self._pb_pids = PB_Pids()

        self._sio = socketio.AsyncClient(logger=False)
        self._sio_events = SioEvents(self)
        self._sio.register_namespace(self._sio_events)

        pb_message_handlers = {
            reset_uuid: self.handle_reset,
            menu_uuid: self.handle_message_menu,
            pose_order_uuid: self.handle_message_pose,
            state_uuid: self.handle_message_state,
            pose_reached_uuid: self.handle_pose_reached,
            actuators_state_uuid: self.handle_actuators_state,
            pid_uuid: self.handle_pid
        }

        self._pbcom = PBCom(serial_port, serial_baud, pb_message_handlers)

    async def run(self):
        """
        Start copilot.
        """
        self._loop = asyncio.get_running_loop()

        self.retry_connection = True
        await self.try_connect()

        await self._pbcom.send_serial_message(copilot_connected_uuid, None)

        await self._pbcom.run()

    async def try_connect(self):
        """
        Poll to wait for the first connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while self.retry_connection:
            try:
                await self._sio.connect(
                    self._server_url,
                    namespaces=["/copilot"],
                    auth={"id": self._id}
                )
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    @property
    def try_reconnection(self) -> bool:
        """
        Return true if Copilot should continue to try to connect to the `Copilot`,
        false otherwise.
        """
        return self._retry_connection

    @try_reconnection.setter
    def try_reconnection(self, new_value: bool) -> None:
        self._retry_connection = new_value

    @property
    def id(self) -> int:
        return self._id

    @property
    def shell_menu(self) -> models.ShellMenu | None:
        return self._shell_menu

    @property
    def pbcom(self) -> PBCom:
        return self._pbcom

    async def handle_reset(self) -> None:
        """
        Handle reset message. This means that the robot has just booted.

        Send a reset message to all connected clients.
        """
        await self._pbcom.send_serial_message(copilot_connected_uuid, None)
        await self._sio_events.emit("reset")

    @pb_exception_handler
    async def handle_message_menu(self, message: bytes | None = None) -> None:
        """
        Send shell menu received from the robot to connected monitors.
        """
        pb_menu = PB_Menu()

        if message:
            await self._loop.run_in_executor(None, pb_menu.ParseFromString, message)

        menu = MessageToDict(pb_menu)
        self._shell_menu = models.ShellMenu.model_validate(menu)
        if self._sio.connected:
            await self._sio_events.emit("menu", self._shell_menu.model_dump(exclude_defaults=True, exclude_unset=True))

    @pb_exception_handler
    async def handle_message_pose(self, message: bytes | None = None) -> None:
        """
        Send robot pose received from the robot to connected monitors and detector.
        """
        pb_pose = PB_Pose()

        if message:
            await self._loop.run_in_executor(None, pb_pose.ParseFromString, message)

        pose = MessageToDict(
            pb_pose,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True
        )
        if self._sio.connected:
            await self._sio_events.emit("pose", pose)

    @pb_exception_handler
    async def handle_message_state(self, message: bytes | None = None) -> None:
        """
        Send robot state received from the robot to connected monitors.
        """
        pb_state = PB_State()

        if message:
            await self._loop.run_in_executor(None, pb_state.ParseFromString, message)

        state = MessageToDict(
            pb_state,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True
        )
        if self._sio.connected:
            await self._sio_events.emit("state", state)

    @pb_exception_handler
    async def handle_actuators_state(self, message: bytes | None = None) -> None:
        """
        Send actuators state received from the robot to connected monitors.
        """
        pb_actuators_state = PB_ActuatorsState()

        if message:
            await self._loop.run_in_executor(None, pb_actuators_state.ParseFromString, message)

        actuators_state = MessageToDict(
            pb_actuators_state,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True
        )
        if self._sio.connected:
            actuators_state["robot_id"] = self._id
            await self._sio_events.emit("actuators_state", actuators_state)

    @pb_exception_handler
    async def handle_pid(self, message: bytes | None = None) -> None:
        """
        Send pids state received from the robot to connected dashboards.
        """
        self._pb_pids = PB_Pids()
        if message:
            await self._loop.run_in_executor(None, self._pb_pids.ParseFromString, message)

        pid_list: list[Pid] = []
        for pb_pid in self._pb_pids.pids:
            pid_list.append(
                Pid(
                    id=pb_pid.id,
                    kp=pb_pid.kp,
                    ki=pb_pid.ki,
                    kd=pb_pid.kd,
                    integral_term_limit=pb_pid.integral_term_limit
                )
            )
        pids = Pids(pids=pid_list)

        # Get JSON Schema
        pids_schema = pids.model_json_schema()
        # Add namespace in JSON Schema
        pids_schema["namespace"] = "/copilot"
        # Add current values in JSON Schema
        values = []
        for pid in pids.pids:
            pid_schema = copy.deepcopy(pid.model_json_schema())
            pid_schema["title"] = pid.id.name
            for prop, value in pid.model_dump().items():
                if prop == "id":
                    continue
                pid_schema["properties"][prop]["value"] = value
            values.append(pid_schema)
        pids_schema["properties"]["pids"]["value"] = values
        # Send config
        await self._sio_events.emit("config", pids_schema)

    async def handle_pose_reached(self) -> None:
        """
        Handle pose reached message.

        Forward info to the planner.
        """
        if self._sio.connected:
            await self._sio_events.emit("pose_reached")

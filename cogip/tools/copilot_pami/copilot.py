import asyncio
import time
from pathlib import Path

import socketio
from google.protobuf.json_format import MessageToDict

from cogip import models
from cogip.models.actuators import ActuatorsKindEnum
from cogip.protobuf import PB_ActuatorState, PB_Menu, PB_Pid, PB_PidEnum, PB_Pose, PB_State
from .pbcom import PBCom, pb_exception_handler
from .pid import Pid
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
actuator_state_uuid: int = 1538397045
actuator_command_uuid: int = 2552455996
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

    _loop: asyncio.AbstractEventLoop = None  # Event loop to use for all coroutines

    def __init__(self, server_url: str, id: int, serial_port: Path, serial_baud: int):
        """
        Class constructor.

        Arguments:
            server_url: server URL
            id: robot id
            serial_port: serial port connected to STM32 device
            serial_baud: baud rate
        """
        self.server_url = server_url
        self.id = id
        self.retry_connection = True
        self.shell_menu: models.ShellMenu | None = None
        self.pb_pids: dict[PB_PidEnum, PB_Pid] = {}

        self.sio = socketio.AsyncClient(logger=False)
        self.sio_events = SioEvents(self)
        self.sio.register_namespace(self.sio_events)

        pb_message_handlers = {
            reset_uuid: self.handle_reset,
            menu_uuid: self.handle_message_menu,
            pose_order_uuid: self.handle_message_pose,
            state_uuid: self.handle_message_state,
            pose_reached_uuid: self.handle_pose_reached,
            actuator_state_uuid: self.handle_actuator_state,
            pid_uuid: self.handle_pid,
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
                await self.sio.connect(self.server_url, namespaces=["/copilot"])
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    @property
    def pbcom(self) -> PBCom:
        return self._pbcom

    async def handle_reset(self) -> None:
        """
        Handle reset message. This means that the robot has just booted.

        Send a reset message to all connected clients.
        """
        await self._pbcom.send_serial_message(copilot_connected_uuid, None)
        await self.sio_events.emit("reset")

    @pb_exception_handler
    async def handle_message_menu(self, message: bytes | None = None) -> None:
        """
        Send shell menu received from the robot to connected monitors.
        """
        pb_menu = PB_Menu()

        if message:
            await self._loop.run_in_executor(None, pb_menu.ParseFromString, message)

        menu = MessageToDict(pb_menu)
        self.shell_menu = models.ShellMenu.model_validate(menu)
        if self.sio.connected:
            await self.sio_events.emit("menu", self.shell_menu.model_dump(exclude_defaults=True, exclude_unset=True))

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
            use_integers_for_enums=True,
        )
        if self.sio.connected:
            await self.sio_events.emit("pose", pose)

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
            use_integers_for_enums=True,
        )
        if self.sio.connected:
            await self.sio_events.emit("state", state)

    @pb_exception_handler
    async def handle_actuator_state(self, message: bytes | None = None) -> None:
        """
        Send actuator state received from the robot.
        """
        pb_actuator_state = PB_ActuatorState()

        if message:
            await self._loop.run_in_executor(None, pb_actuator_state.ParseFromString, message)

        kind = pb_actuator_state.WhichOneof("type")
        actuator_state = MessageToDict(
            getattr(pb_actuator_state, kind),
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            use_integers_for_enums=True,
        )
        actuator_state["kind"] = ActuatorsKindEnum[kind]
        if self.sio.connected:
            await self.sio_events.emit("actuator_state", actuator_state)

    @pb_exception_handler
    async def handle_pid(self, message: bytes | None = None) -> None:
        """
        Send pids state received from the robot to connected dashboards.
        """
        pb_pid = PB_Pid()
        if message:
            await self._loop.run_in_executor(None, pb_pid.ParseFromString, message)

        self.pb_pids[pb_pid.id] = pb_pid
        pid = Pid(
            id=pb_pid.id,
            kp=pb_pid.kp,
            ki=pb_pid.ki,
            kd=pb_pid.kd,
            integral_term_limit=pb_pid.integral_term_limit,
        )

        # Get JSON Schema
        pid_schema = pid.model_json_schema()
        # Add namespace in JSON Schema
        pid_schema["namespace"] = "/copilot"
        # Add current values in JSON Schema
        pid_schema["title"] = pid.id.name
        for prop, value in pid.model_dump().items():
            if prop == "id":
                continue
            pid_schema["properties"][prop]["value"] = value
            pid_schema["properties"][f"{pid.id}-{prop}"] = pid_schema["properties"][prop]
            del pid_schema["properties"][prop]
        # Send config
        await self.sio_events.emit("config", pid_schema)

    async def handle_pose_reached(self) -> None:
        """
        Handle pose reached message.

        Forward info to the planner.
        """
        if self.sio.connected:
            await self.sio_events.emit("pose_reached")

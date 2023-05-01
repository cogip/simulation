from functools import partial
import math
from multiprocessing import Manager, Process
from multiprocessing.managers import DictProxy
import threading
import time
from typing import Any

import socketio

from cogip import models
from cogip.tools.copilot.controller import ControllerEnum
from cogip.utils import ThreadLoop
from . import actions, logger, menu, pose, sio_events
from .camp import Camp
from .context import GameContext
from .properties import Properties
from .robot import Robot
from .table import TableEnum
from .strategy import Strategy
from .avoidance.avoidance import AvoidanceStrategy
from .avoidance.process import avoidance_process
from .wizard import GameWizard


class Planner:
    """
    Main planner class.
    """

    def __init__(
            self,
            server_url: str,
            robot_width: int,
            obstacle_radius: int,
            obstacle_bb_margin: float,
            obstacle_bb_vertices: int,
            max_distance: int,
            obstacle_sender_interval: float,
            path_refresh_interval: float,
            plot: bool):
        """
        Class constructor.

        Arguments:
            server_url: Server URL
            robot_width: Width of the robot (in )
            obstacle_radius: Radius of a dynamic obstacle (in mm)
            obstacle_bb_margin: Obstacle bounding box margin in percent of the radius
            obstacle_bb_vertices: Number of obstacle bounding box vertices
            max_distance: Maximum distance to take avoidance points into account (mm)
            obstacle_sender_interval: Interval between each send of obstacles to dashboards (in seconds)
            path_refresh_interval: Interval between each update of robot paths (in seconds)
            plot: Display avoidance graph in realtime
        """
        self._server_url = server_url
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
        self._sio = socketio.Client(logger=False)
        self._sio_ns = sio_events.SioEvents(self)
        self._sio.register_namespace(self._sio_ns)
        self._camp = Camp()
        self._game_context = GameContext()
        self._robots: dict[int, Robot] = {}
        self._start_positions: dict[int, int] = {}
        self._actions = actions.action_classes.get(self._game_context.strategy, actions.Actions)()
        self._obstacles: dict[int, models.DynObstacleList] = {}
        self._start_pose_menu_entries: dict[int, models.MenuEntry] = {}
        self._obstacles_sender_loop = ThreadLoop(
            "Obstacles sender loop",
            obstacle_sender_interval,
            self.send_obstacles,
            logger=True
        )
        self._game_wizard = GameWizard(self)
        self._process_manager = Manager()
        self._shared_exiting: DictProxy = self._process_manager.dict()
        self._shared_poses_current: DictProxy = self._process_manager.dict()
        self._shared_poses_order: DictProxy = self._process_manager.dict()
        self._shared_obstacles: DictProxy = self._process_manager.dict()
        self._shared_last_avoidance_pose_currents: DictProxy = self._process_manager.dict()
        self._queue_sio = self._process_manager.Queue()
        self._avoidance_processes: dict[int, Process] = {}
        self._shared_properties: DictProxy = self._process_manager.dict({
            "controllers": {},
            "path_refresh_interval": path_refresh_interval,
            "robot_width": robot_width,
            "obstacle_radius": obstacle_radius,
            "obstacle_bb_vertices": obstacle_bb_vertices,
            "obstacle_bb_margin": obstacle_bb_margin,
            "max_distance": max_distance,
            "plot": plot
        })

        self._thread_sio = threading.Thread(target=self.thread_sio).start()

    def connect(self):
        """
        Connect to SocketIO server.
        """
        self.retry_connection = True
        threading.Thread(target=self.try_connect).start()

    def try_connect(self):
        """
        Poll to wait for the first connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while (self.retry_connection):
            try:
                self._sio.connect(
                    self._server_url,
                    socketio_path="sio/socket.io",
                    namespaces=["/planner"]
                )
            except socketio.exceptions.ConnectionError:
                time.sleep(2)
                continue
            break

    @property
    def try_reconnection(self) -> bool:
        """
        Return true if Planner should continue to try to connect to the server,
        false otherwise.
        """
        return self._retry_connection

    @try_reconnection.setter
    def try_reconnection(self, new_value: bool) -> None:
        self._retry_connection = new_value

    def start(self) -> None:
        """
        Start sending obstacles list.
        """
        self._obstacles_sender_loop.start()

    def stop(self) -> None:
        """
        Stop sending obstacles list.
        """
        self._obstacles_sender_loop.stop()

    def thread_sio(self):
        while True:
            name, message = self._queue_sio.get()
            robot_id, value = message

            if not (robot := self._robots.get(robot_id)):
                return

            match name:
                case "path":
                    robot.avoidance_path = [pose.Pose.parse_obj(m) for m in value[1:]]
                    if len(value):
                        self._sio_ns.emit(name, (robot_id, value))
                case "set_controller":
                    robot.controller = ControllerEnum(value)
                case _:
                    self._sio_ns.emit(name, message)

    def add_robot(self, robot_id: int, virtual: bool) -> None:
        """
        Add a new robot.
        """
        if robot_id in self._robots:
            self.del_robot(robot_id)
        self._robots[robot_id] = (robot := Robot(robot_id, self, virtual))
        self._sio_ns.emit("starter_changed", (robot_id, robot.starter.is_pressed))
        new_start_pose = self._start_positions.get(robot_id, robot_id)
        available_start_poses = self._game_context.get_available_start_poses()
        if new_start_pose not in available_start_poses:
            new_start_pose = available_start_poses[(robot_id - 1) % len(available_start_poses)]
        robot.set_pose_start(self._game_context.get_start_pose((new_start_pose)))
        self._shared_properties["controllers"][robot_id] = robot.controller
        self._shared_exiting[robot_id] = False
        self._shared_obstacles[robot_id] = []
        self._avoidance_processes[robot_id] = Process(target=avoidance_process, args=(
            robot_id,
            self._game_context.strategy,
            self._game_context.avoidance_strategy,
            self._game_context.table,
            self._shared_properties,
            self._shared_exiting,
            self._shared_poses_current,
            self._shared_poses_order,
            self._shared_obstacles,
            self._shared_last_avoidance_pose_currents,
            self._queue_sio
        ))
        self._avoidance_processes[robot_id].start()
        self.update_start_pose_commands()
        self._sio_ns.emit("set_controller", (robot_id, robot.controller.value))

    def del_robot(self, robot_id: int) -> None:
        """
        Remove a robot.
        """
        self._robots[robot_id].starter.close()
        if robot_id in self._shared_properties["controllers"]:
            del self._shared_properties["controllers"][robot_id]
        if robot_id in self._shared_obstacles:
            del self._shared_obstacles[robot_id]
        if robot_id in self._shared_exiting:
            self._shared_exiting[robot_id] = True
        if robot_id in self._avoidance_processes:
            self._avoidance_processes[robot_id].join()
            del self._avoidance_processes[robot_id]
        if robot_id in self._robots:
            del self._robots[robot_id]
        self.update_start_pose_commands()

    def starter_changed(self, robot_id: int, pushed: bool) -> None:
        if not (robot := self._robots.get(robot_id)):
            return
        if not robot.virtual:
            self._sio_ns.emit("starter_changed", (robot_id, pushed))
        if pushed:
            self._sio_ns.emit("game_reset", robot_id)

    def update_start_pose_commands(self):
        """
        Update menu commands to to choose start pose for each robot.
        """
        for robot_id, menu_cmd in self._start_pose_menu_entries.items():
            menu.menu.entries.remove(menu_cmd)
            if hasattr(self, cmd := f"cmd_choose_start_position_{robot_id}"):
                delattr(self, cmd)
        self._start_pose_menu_entries.clear()

        for robot_id in sorted(self._robots.keys(), reverse=True):
            func_name = f"choose_start_position_{robot_id}"
            menu_entry = models.MenuEntry(
                cmd=func_name,
                desc=f"Choose Start Position {robot_id}"
            )
            menu.menu.entries.insert(0, menu_entry)
            self._start_pose_menu_entries[robot_id] = menu_entry
            setattr(self, "cmd_" + func_name, partial(self.cmd_choose_start_position, robot_id))
            self._sio_ns.emit("register_menu", {"name": "planner", "menu": menu.menu.dict()})

    def reset(self) -> None:
        """
        Reset planner, context, robots and actions.
        """
        self._game_context.reset()
        self._actions = actions.action_classes.get(self._game_context.strategy, actions.Actions)()

        # Remove robots and add them again to reset all robots.
        robots = {robot_id: robot.virtual for robot_id, robot in self._robots.items()}
        for robot_id, _ in robots.items():
            self.del_robot(robot_id)
        for robot_id, virtual in robots.items():
            self.add_robot(robot_id, virtual)

    def reset_controllers(self):
        new_controller = self._game_context.default_controller
        for robot_id, robot in self._robots.items():
            if robot.controller == new_controller:
                continue
            robot.controller = new_controller
            self._sio_ns.emit("set_controller", (robot_id, new_controller.value))

    def set_pose_start(self, robot_id: int, pose_start: pose.Pose):
        """
        Set the start position of the robot for the next game.
        """
        self._sio_ns.emit("pose_start", (robot_id, pose_start.pose.dict()))

    def set_pose_order(self, robot_id: int, pose_order: pose.Pose):
        """
        Set the current position order of the robot.
        """
        if not (robot := self._robots.get(robot_id)):
            return

        robot.pose_order = pose_order

        if self._game_context.strategy in [Strategy.LinearSpeedTest, Strategy.AngularSpeedTest]:
            self._sio_ns.emit("pose_order", (robot_id, pose_order.pose.dict()))

    def set_pose_current(self, robot_id: int, pose: models.Pose) -> None:
        """
        Set current pose of a robot.
        """
        if not (robot := self._robots.get(robot_id)):
            return
        robot.pose_current = models.Pose.parse_obj(pose)

    def set_pose_reached(self, robot_id: int) -> None:
        """
        Set pose reached for a robot.
        """
        if not (robot := self._robots.get(robot_id)):
            return

        if robot_id in self._shared_last_avoidance_pose_currents:
            del self._shared_last_avoidance_pose_currents[robot_id]

        if len(robot.avoidance_path) > 2:
            # The pose reached is intermediate, do nothing.
            return

        # Set pose reached
        robot.pose_reached = True

        if not self._game_context.playing:
            return

        self.next_pose(robot_id)

    def next_pose(self, robot_id: int):
        """
        Select the next pose for a robot.
        """
        if not (robot := self._robots.get(robot_id)):
            return

        # Get and set new pose
        new_pose_order = robot.next_pose()

        # If no pose left in current action, get and set new action
        if not new_pose_order and (new_action := self.get_action(robot_id)):
            robot.set_action(new_action)

    def game_end(self, robot_id: int):
        self.cmd_stop()
        self._sio_ns.emit("score", self._game_context.score)

    def get_action(self, robot_id: int) -> actions.Action | None:
        """
        Get a new action for a robot.
        Simply choose next action in the list for now.
        """
        if not (robot := self._robots.get(robot_id)):
            return

        if len(self._actions) == 0:
            return None

        action = self._actions.pop(0)
        action.robot = robot
        return action

    def create_dyn_obstacle(
            self,
            center: models.Vertex,
            radius: float | None = None,
            bb_radius: float | None = None) -> models.DynRoundObstacle:
        """
        Create a dynamic obstacle.

        Arguments:
            center: center of the obstacle
            radius: radius of the obstacle, use the value from global properties if not specified
            bb_radius: radius of the bounding box
        """
        if radius is None:
            radius = self._properties.obstacle_radius

        if bb_radius is None:
            bb_radius = radius + self._properties.robot_width / 2

        bb = [
            models.Vertex(
                x=center.x + bb_radius * math.cos(
                    (tmp := (i * 2 * math.pi) / self._properties.obstacle_bb_vertices)
                ),
                y=center.y + bb_radius * math.sin(tmp),
            )
            for i in reversed(range(self._properties.obstacle_bb_vertices))
        ]

        return models.DynRoundObstacle(
            x=center.x,
            y=center.y,
            radius=radius,
            bb=bb
        )

    def set_obstacles(self, robot_id: int, obstacles: list[models.Vertex]) -> None:
        """
        Store obstacles detected by a robot sent by Detector.
        Add bounding box and radius.
        """
        if not (robot := self._robots.get(robot_id)):
            return

        bb_radius = self._properties.obstacle_radius + self._properties.robot_width / 2

        robot.obstacles = [
            self.create_dyn_obstacle(obstacle, bb_radius)
            for obstacle in obstacles
        ]

    @property
    def all_obstacles(self) -> models.DynObstacleList:
        return sum([robot.obstacles for robot in self._robots.values()], start=[])

    def send_obstacles(self) -> None:
        self._sio_ns.emit("obstacles", [o.dict(exclude_defaults=True) for o in self.all_obstacles])

    def command(self, cmd: str) -> None:
        """
        Execute a command from the menu.
        """
        if cmd.startswith("wizard_"):
            self.cmd_wizard_test(cmd)
            return

        if cmd == "config":
            # Get JSON Schema
            schema = self._properties.schema()
            # Add namespace in JSON Schema
            schema["namespace"] = "/planner"
            # Add current values in JSON Schema
            for prop, value in self._properties.dict().items():
                schema["properties"][prop]["value"] = value
            # Send config
            self._sio_ns.emit("config", schema)
            return

        if cmd == "game_wizard":
            self._game_wizard.start()
            return

        if not (cmd_func := getattr(self, f"cmd_{cmd}", None)):
            logger.warning(f"Unknown command: {cmd}")
            return

        cmd_func()

    def update_config(self, config: dict[str, Any]) -> None:
        """
        Update a Planner property with the value sent by the dashboard.
        """
        self._properties.__setattr__(name := config["name"], value := config["value"])
        if name in self._shared_properties:
            self._shared_properties[name] = value
        match name:
            case "obstacle_sender_interval":
                self._obstacles_sender_loop.interval = self._properties.path_refresh_interval
            case "path_refresh_interval":
                for thread in self._avoidance_path_updaters.values():
                    thread.interval = self._properties.path_refresh_interval

    def cmd_play(self) -> None:
        """
        Play command from the menu.
        """
        if self._game_context.playing:
            return

        self._game_context.playing = True
        list(map(self.set_pose_reached, self._robots.keys()))

    def cmd_stop(self) -> None:
        """
        Stop command from the menu.
        """
        self._game_context.playing = False

    def cmd_next(self) -> None:
        """
        Next command from the menu.
        Ignored if current pose is not reached for all robots.
        """
        if self._game_context.playing:
            return

        # Check that pose_reached is set for all robots
        if not all([robot.pose_reached for robot in self._robots.values()]):
            return

        list(map(self.next_pose, self._robots.keys()))

    def cmd_reset(self) -> None:
        """
        Reset command from the menu.
        """
        self.reset()
        self._sio_ns.emit("cmd_reset")

    def cmd_choose_camp(self) -> None:
        """
        Choose camp command from the menu.
        Send camp wizard message.
        """
        self._sio_ns.emit(
            "wizard",
            {
                "name": "Choose Camp",
                "type": "camp",
                "value": self._camp.color.name
            }
        )

    def cmd_choose_strategy(self) -> None:
        """
        Choose strategy command from the menu.
        Send strategy wizard message.
        """
        self._sio_ns.emit(
            "wizard",
            {
                "name": "Choose Strategy",
                "type": "choice_str",
                "choices": [e.name for e in Strategy],
                "value": self._game_context.strategy.name
            }
        )

    def cmd_choose_avoidance(self) -> None:
        """
        Choose avoidance strategy command from the menu.
        Send avoidance strategy wizard message.
        """
        self._sio_ns.emit(
            "wizard",
            {
                "name": "Choose Avoidance",
                "type": "choice_str",
                "choices": [e.name for e in AvoidanceStrategy],
                "value": self._game_context.avoidance_strategy.name
            }
        )

    def cmd_choose_start_position(self, robot_id) -> None:
        """
        Choose start position command from the menu.
        Send start position wizard message.
        """
        self._sio_ns.emit(
            "wizard",
            {
                "name": f"Choose Start Position {robot_id}",
                "type": "choice_integer",
                "choices": self._game_context.get_available_start_poses(),
                "value": self._start_positions.get(robot_id, robot_id),
                "robot_id": robot_id
            }
        )

    def cmd_choose_table(self) -> None:
        """
        Choose table command from the menu.
        Send table wizard message.
        """
        self._sio_ns.emit(
            "wizard",
            {
                "name": "Choose Table",
                "type": "choice_str",
                "choices": [e.name for e in TableEnum],
                "value": self._game_context._table.name
            }
        )

    def wizard_response(self, message: dict[str, Any]) -> None:
        """
        Handle wizard response sent from the dashboard.
        """
        if (value := message["value"]) is None:
            return

        match name := message.get("name"):
            case "Choose Camp":
                new_camp = Camp.Colors[value]
                if self._camp.color == new_camp:
                    return
                self._camp.color = new_camp
                self.reset()
                logger.info(f"Wizard: New camp: {self._camp.color.name}")
            case "Choose Strategy":
                new_strategy = Strategy[value]
                if self._game_context.strategy == new_strategy:
                    return
                self._game_context.strategy = new_strategy
                self.reset()
                self.reset_controllers()
                logger.info(f'Wizard: New strategy: {self._game_context.strategy.name}')
            case "Choose Avoidance":
                new_strategy = AvoidanceStrategy[value]
                if self._game_context.avoidance_strategy == new_strategy:
                    return
                self._game_context.avoidance_strategy = new_strategy
                self.reset()
                logger.info(f'Wizard: New avoidance strategy: {self._game_context.avoidance_strategy.name}')
            case chose_start_pose if chose_start_pose.startswith("Choose Start Position"):
                if robot := self._robots.get(robot_id := message.get("robot_id")):
                    start_position = int(value)
                    self._start_positions[robot_id] = start_position
                    robot.set_pose_start(self._game_context.get_start_pose(start_position))
            case "Choose Table":
                new_table = TableEnum[value]
                if self._game_context.table == new_table:
                    return
                self._game_context.table = new_table
                self._shared_properties["table"] = new_table
                self.reset()
                logger.info(f'Wizard: New table: {self._game_context._table.name}')
            case game_wizard_response if game_wizard_response.startswith("Game Wizard"):
                self._game_wizard.response(message)
            case wizard_test_response if wizard_test_response.startswith("Wizard Test"):
                logger.info(f"Wizard test response: {name} = {value}")
            case _:
                logger.warning(f"Wizard: Unknown type: {name}")

    def cmd_wizard_test(self, cmd: str):
        match cmd:
            case "wizard_boolean":
                message = {
                    "name": "Wizard Test Boolean",
                    "type": "boolean",
                    "value": True
                }
            case "wizard_integer":
                message = {
                    "name": "Wizard Test Integer",
                    "type": "integer",
                    "value": 42
                }
            case "wizard_floating":
                message = {
                    "name": "Wizard Test Float",
                    "type": "floating",
                    "value": 66.6
                }
            case "wizard_str":
                message = {
                    "name": "Wizard Test String",
                    "type": "str",
                    "value": "cogip"
                }
            case "wizard_message":
                message = {
                    "name": "Wizard Test Message",
                    "type": "message",
                    "value": "Hello Robot!"
                }
            case "wizard_choice_integer":
                message = {
                    "name": "Wizard Test Choice Integer",
                    "type": "choice_integer",
                    "choices": [1, 2, 3],
                    "value": 2
                }
            case "wizard_choice_floating":
                message = {
                    "name": "Wizard Test Choice Float",
                    "type": "choice_floating",
                    "choices": [1.1, 2.2, 3.3],
                    "value": 2.2
                }
            case "wizard_choice_str":
                message = {
                    "name": "Wizard Test Choice String",
                    "type": "choice_str",
                    "choices": ["one", "two", "tree"],
                    "value": "two"
                }
            case "wizard_select_integer":
                message = {
                    "name": "Wizard Test Select Integer",
                    "type": "select_integer",
                    "choices": [1, 2, 3],
                    "value": [1, 3]
                }
            case "wizard_select_floating":
                message = {
                    "name": "Wizard Test Select Float",
                    "type": "select_floating",
                    "choices": [1.1, 2.2, 3.3],
                    "value": [1.1, 3.3]
                }
            case "wizard_select_str":
                message = {
                    "name": "Wizard Test Select String",
                    "type": "select_str",
                    "choices": ["one", "two", "tree"],
                    "value": ["one", "tree"]
                }
            case "wizard_camp":
                message = {
                    "name": "Wizard Test Camp",
                    "type": "camp",
                    "value": "green"
                }
            case "wizard_camera":
                message = {
                    "name": "Wizard Test Camera",
                    "type": "camera"
                }
            case "wizard_score":
                self._sio_ns.emit("score", 100)
                return
            case _:
                logger.warning(f"Wizard test unsupported: {cmd}")
                return

        self._sio_ns.emit("wizard", message)

from functools import partial
import math
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
from .strategy import Strategy


class Planner:
    """
    Main planner class.
    """

    def __init__(
            self,
            server_url: str,
            obstacle_radius: int,
            obstacle_bb_margin: float,
            obstacle_bb_vertices: int,
            obstacle_sender_interval: float,
            path_refresh_interval: float):
        """
        Class constructor.

        Arguments:
            server_url: Server URL
            obstacle_radius: Radius of a dynamic obstacle
            obstacle_bb_margin: Obstacle bounding box margin in percent of the radius
            obstacle_bb_vertices: Number of obstacle bounding box vertices
            obstacle_sender_interval: Interval between each send of obstacles to dashboards (in seconds)
            path_refresh_interval: Interval between each update of robot paths (in seconds)
        """
        self._server_url = server_url
        self._properties = Properties(
            obstacle_radius=obstacle_radius,
            obstacle_bb_margin=obstacle_bb_margin,
            obstacle_bb_vertices=obstacle_bb_vertices,
            obstacle_sender_interval=obstacle_sender_interval,
            path_refresh_interval=path_refresh_interval
        )
        self._retry_connection = True
        self._sio = socketio.Client(logger=False)
        self._sio_ns = sio_events.SioEvents(self)
        self._sio.register_namespace(self._sio_ns)
        self._camp = Camp()
        self._game_context = GameContext()
        self._robots: dict[int, Robot] = {}
        self._start_positions: dict[int, int] = {}
        self._pose_orders: dict[int, pose.Pose] = {}
        self._actions = actions.action_classes.get(self._game_context.strategy, actions.Actions)()
        self._obstacles: dict[int, models.DynObstacleList] = {}
        self._start_pose_menu_entries: dict[int, models.MenuEntry] = {}
        self._avoidance_path_updaters: dict[int, ThreadLoop] = {}
        self._obstacles_sender_loop = ThreadLoop(
            "Obstacles sender loop",
            obstacle_sender_interval,
            self.send_obstacles,
            logger=True
        )

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

    def add_robot(self, robot_id: int) -> None:
        """
        Add a new robot.
        """
        if robot_id in self._robots:
            self.del_robot(robot_id)
        self._robots[robot_id] = (robot := Robot(robot_id, self))
        robot.set_pose_start(self._game_context.get_start_pose(self._start_positions.get(robot_id, robot_id)))
        self.update_start_pose_commands()
        self._avoidance_path_updaters[robot_id] = ThreadLoop(
            f"Avoidance path updater {robot_id}",
            self._properties.path_refresh_interval,
            partial(self.update_avoidance_path, robot_id),
            logger=True
        )
        self._avoidance_path_updaters[robot_id].start()
        self._sio_ns.emit("set_controller", (robot_id, robot.controller.value))

    def del_robot(self, robot_id: int) -> None:
        """
        Remove a robot.
        """
        del self._robots[robot_id]
        self.update_start_pose_commands()
        self._avoidance_path_updaters[robot_id].stop()
        del self._avoidance_path_updaters[robot_id]

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
        robot_ids = list(self._robots.keys())
        for robot_id in robot_ids:
            self.del_robot(robot_id)
        for robot_id in robot_ids:
            self.add_robot(robot_id)

    def reset_controllers(self):
        new_controller = self._game_context.default_controller
        for robot_id, robot in self._robots:
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
        self._pose_orders[robot_id] = pose_order
        self._sio_ns.emit("pose_order", (robot_id, pose_order.pose.dict()))
        self._sio_ns.emit(
            "path", (robot_id, [self._robots[robot_id].pose_current.dict(), pose_order.pose.dict()])
        )

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

    def set_obstacles(self, robot_id: int, obstacles: list[models.Vertex]) -> None:
        """
        Store obstacles detected by a robot sent by Detector.
        Add bounding box and radius.
        """
        if not (robot := self._robots.get(robot_id)):
            return

        robot.obstacles = []

        bb_radius = self._properties.obstacle_radius * (1 + self._properties.obstacle_bb_margin)
        for obstacle in obstacles:
            radius = self._properties.obstacle_radius
            bb = [
                models.Vertex(
                    x=obstacle.x + bb_radius * math.cos(
                        (tmp := (i * 2 * math.pi) / self._properties.obstacle_bb_vertices)
                    ),
                    y=obstacle.y + bb_radius * math.sin(tmp),
                )
                for i in range(self._properties.obstacle_bb_vertices)
            ]
            robot.obstacles.append(models.DynRoundObstacle(
                x=obstacle.x,
                y=obstacle.y,
                radius=radius,
                bb=bb
            ))

    @property
    def all_obstacles(self) -> list[models.DynObstacleList]:
        return sum([robot.obstacles for robot in self._robots.values()], start=[])

    def send_obstacles(self) -> None:
        self._sio_ns.emit("obstacles", [o.dict(exclude_defaults=True) for o in self.all_obstacles])

    def update_avoidance_path(self, robot_id: int):
        """
        Compute avoidance path for a robot, given its current pose, pose order and obstacles.
        """
        pass

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

        if not (cmd_func := getattr(self, f"cmd_{cmd}", None)):
            logger.warning(f"Unknown command: {cmd}")
            return

        cmd_func()

    def update_config(self, config: dict[str, Any]) -> None:
        """
        Update a Planner property with the value sent by the dashboard.
        """
        self._properties.__setattr__(name := config["name"], config["value"])
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
                "choices": list(range(1, 6)),
                "value": self._start_positions.get(robot_id, robot_id),
                "robot_id": robot_id
            }
        )

    def wizard_response(self, message: dict[str, Any]) -> None:
        """
        Handle wizard response sent from the dashboard.
        """
        match name := message.get("name"):
            case "Choose Camp":
                new_camp = Camp.Colors[message["value"]]
                if self._camp.color == new_camp:
                    return
                self._camp.color = new_camp
                self.reset()
                logger.info(f"Wizard: New camp: {self._camp.color.name}")
            case "Choose Strategy":
                new_strategy = Strategy[message["value"]]
                if self._game_context.strategy == new_strategy:
                    return
                self._game_context.strategy = new_strategy
                self.reset()
                self.reset_controllers()
                logger.info(f'Wizard: New strategy: {self._game_context.strategy.name}')
            case chose_start_pose if chose_start_pose.startswith("Choose Start Position"):
                if robot := self._robots.get(robot_id := message.get("robot_id")):
                    start_position = int(message["value"])
                    self._start_positions[robot_id] = start_position
                    robot.set_pose_start(self._game_context.get_start_pose(start_position))
            case wizard_test_response if wizard_test_response.startswith("Wizard Test"):
                logger.info(f"Wizard test response: {name} = {message['value']}")
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
            case _:
                logger.warning(f"Wizard test unsupported: {cmd}")
                return

        self._sio_ns.emit("wizard", message)

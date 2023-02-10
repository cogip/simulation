from functools import partial
import threading
import time
from typing import Any

import socketio

from cogip import models
from cogip.utils import ThreadLoop
from . import actions, logger, menu, sio_events
from .camp import Camp
from .context import GameContext
from .robot import Robot
from .strategy import Strategy


class Planner:
    """
    Main planner class.
    """

    def __init__(
            self,
            server_url: str):
        """
        Class constructor.

        Arguments:
            server_url: Server URL
        """
        self._server_url = server_url
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
            0.2,
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
        self._robots[robot_id] = (robot := Robot(robot_id, self._sio_ns))
        robot.set_pose_start(self._game_context.get_start_pose(self._start_positions.get(robot_id, robot_id)))
        self.update_start_pose_commands()
        self._obstacles[robot_id] = []

    def del_robot(self, robot_id: int) -> None:
        """
        Remove a robot.
        """
        del self._robots[robot_id]
        self.update_start_pose_commands()

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

    def set_pose_current(self, robot_id: int, pose: models.Pose) -> None:
        """
        Set current pose to reach for a robot.
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

    def set_obstacles(self, robot_id: int, obstacles: models.DynObstacleList) -> None:
        self._obstacles[robot_id] = obstacles

    def send_obstacles(self) -> None:
        all_obstacles = sum(self._obstacles.values(), start=[])
        self._sio_ns.emit("obstacles", [o.dict() for o in all_obstacles])

    def command(self, cmd: str) -> None:
        """
        Execute a command from the menu.
        """
        if not (cmd_func := getattr(self, f"cmd_{cmd}", None)):
            logger.warning(f"Unknown command: {cmd}")
            return

        cmd_func()

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
                logger.info(f'Wizard: New strategy: {self._game_context.strategy.name}')
            case chose_start_pose if chose_start_pose.startswith("Choose Start Position"):
                if robot := self._robots.get(robot_id := message.get("robot_id")):
                    start_position = int(message["value"])
                    self._start_positions[robot_id] = start_position
                    robot.set_pose_start(self._game_context.get_start_pose(start_position))
            case _:
                logger.warning(f"Wizard: Unknown type: {name}")

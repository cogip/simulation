import asyncio
from functools import partial
from multiprocessing import Manager, Process
from multiprocessing.managers import DictProxy
import queue
import time
from typing import Any

import socketio

from cogip import models
from cogip.tools.copilot.controller import ControllerEnum
from cogip.utils.asyncloop import AsyncLoop
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
            plot: bool,
            debug: bool):
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
            debug: enable debug messages
        """
        self._server_url = server_url
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
        self._loop: asyncio.AbstractEventLoop | None = None
        self._retry_connection = True
        self._sio = socketio.AsyncClient(logger=False)
        self._sio_ns = sio_events.SioEvents(self)
        self._sio.register_namespace(self._sio_ns)
        self._camp = Camp()
        self._game_context = GameContext()
        self._robots: dict[int, Robot] = {}
        self._start_positions: dict[int, int] = {}
        self._actions = actions.action_classes.get(self._game_context.strategy, actions.Actions)()
        self._obstacles: dict[int, models.DynObstacleList] = {}
        self._start_pose_menu_entries: dict[int, models.MenuEntry] = {}
        self._obstacles_sender_loop = AsyncLoop(
            "Obstacles sender loop",
            obstacle_sender_interval,
            self.send_obstacles,
            logger=self._debug
        )
        self._game_wizard = GameWizard(self)
        self._process_manager = Manager()
        self._shared_exiting: DictProxy = self._process_manager.dict()
        self._shared_poses_current: DictProxy = self._process_manager.dict()
        self._shared_poses_order: DictProxy = self._process_manager.dict()
        self._shared_obstacles: DictProxy = self._process_manager.dict()
        self._shared_cake_obstacles: DictProxy = self._process_manager.dict()
        self._shared_last_avoidance_pose_currents: DictProxy = self._process_manager.dict()
        self._sio_emitter_queues: dict[int, queue.Queue] = {}
        self._sio_emitter_tasks: dict[int, asyncio.Task] = {}
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
        self._sio_receiver_tasks: dict[int, asyncio.Task] = {}
        self._sio_receiver_queues: dict[int, asyncio.Queue] = {}
        self.update_cake_obstacles()

    async def connect(self):
        """
        Connect to SocketIO server.
        """
        self._loop = asyncio.get_running_loop()

        self.retry_connection = True
        await self.try_connect()
        try:
            await self._sio.wait()
        except asyncio.CancelledError:
            robot_ids = list(self._robots.keys())
            for robot_id in robot_ids:
                await self.del_robot(robot_id)
            self._process_manager.shutdown()

    async def try_connect(self):
        """
        Poll to wait for the first connection.
        Disconnections/reconnections are handle directly by the client.
        """
        while (self.retry_connection):
            try:
                await self._sio.connect(
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

    async def start(self):
        """
        Start sending obstacles list.
        """
        self._obstacles_sender_loop.start()

    async def stop(self):
        """
        Stop running tasks.
        """
        await self._obstacles_sender_loop.stop()

    async def task_sio_emitter(self, robot_id: int):
        logger.debug(f"Robot {robot_id}: Task SIO Emitter started")
        try:
            while True:
                name, value = await asyncio.to_thread(self._sio_emitter_queues[robot_id].get)

                if not (robot := self._robots.get(robot_id)):
                    return

                match name:
                    case "path":
                        if len(value) == 0 and robot.pose_order:
                            robot.blocked += 1
                            robot.avoidance_path = []
                            if robot.blocked > 50:
                                await self.blocked(robot_id)
                                robot.blocked = 0
                        else:
                            robot.blocked = 0
                            robot.avoidance_path = [pose.Pose.parse_obj(m) for m in value[1:]]
                        await self._sio_ns.emit(name, (robot_id, value))
                    case "pose_order":
                        if robot.blocked == 0:
                            await self._sio_ns.emit(name, (robot_id, value))
                            continue

                        # stop_pose = models.PathPose(**robot.pose_current.dict(), allow_reverse=True)
                        # await self._sio_ns.emit("pose_order", (robot_id, stop_pose.pose.dict()))

                    case "set_controller":
                        robot.controller = ControllerEnum(value)
                    case "starter_changed":
                        await self.starter_changed(robot.robot_id, value)
                    case _:
                        await self._sio_ns.emit(name, (robot_id, value))
        except asyncio.CancelledError:
            logger.debug(f"Robot {robot_id}: Task SIO Emitter cancelled")
            raise

    async def task_sio_receiver(self, robot_id: id, queue: asyncio.Queue):
        logger.debug(f"Robot {robot_id}: Task SIO Receiver started")
        try:
            while True:
                func = await queue.get()
                await func
        except asyncio.CancelledError:
            logger.debug(f"Robot {robot_id}: Task SIO Receiver cancelled")
            raise

    async def add_robot(self, robot_id: int, virtual: bool):
        """
        Add a new robot.
        """
        if robot_id in self._robots:
            await self.del_robot(robot_id)
        logger.debug(f"Robot {robot_id}: add")

        self._robots[robot_id] = (robot := Robot(robot_id, self, virtual))
        self._sio_receiver_queues[robot_id] = asyncio.Queue()
        self._sio_receiver_tasks[robot_id] = asyncio.create_task(
            self.task_sio_receiver(robot_id, self._sio_receiver_queues[robot_id])
        )
        await self._sio_ns.emit("starter_changed", (robot_id, robot.starter.is_pressed))
        new_start_pose = self._start_positions.get(robot_id, robot_id)
        available_start_poses = self._game_context.get_available_start_poses()
        if new_start_pose not in available_start_poses:
            new_start_pose = available_start_poses[(robot_id - 1) % len(available_start_poses)]
        await robot.set_pose_start(self._game_context.get_start_pose(new_start_pose).pose)
        self._shared_properties["controllers"][robot_id] = robot.controller
        self._shared_exiting[robot_id] = False
        self._shared_obstacles[robot_id] = []
        self._shared_cake_obstacles[robot_id] = []
        self._sio_emitter_queues[robot_id] = self._process_manager.Queue()
        self._sio_emitter_tasks[robot_id] = asyncio.create_task(
            self.task_sio_emitter(robot_id), name=f"Robot {robot_id}: Task SIO Emitter"
        )
        self.update_cake_obstacles(robot_id)
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
            self._shared_cake_obstacles,
            self._shared_last_avoidance_pose_currents,
            self._sio_emitter_queues[robot_id]
        ))
        self._avoidance_processes[robot_id].start()
        await self.update_start_pose_commands()
        await self._sio_ns.emit("set_controller", (robot_id, robot.controller.value))

    async def del_robot(self, robot_id: int):
        """
        Remove a robot.
        """
        logger.debug(f"Robot {robot_id}: delete")
        self._robots[robot_id].starter.close()
        if robot_id in self._shared_properties["controllers"]:
            del self._shared_properties["controllers"][robot_id]
        if robot_id in self._shared_obstacles:
            del self._shared_obstacles[robot_id]
        if robot_id in self._avoidance_processes:
            self._shared_exiting[robot_id] = True
            self._avoidance_processes[robot_id].join()
            del self._avoidance_processes[robot_id]
        if task := self._sio_emitter_tasks.get(robot_id):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug(f"Robot {robot_id}: Task SIO Emitter stopped")
            del self._sio_emitter_tasks[robot_id]
        if robot_id in self._sio_emitter_queues:
            del self._sio_emitter_queues[robot_id]
        if robot_id in self._robots:
            del self._robots[robot_id]
        if task := self._sio_receiver_tasks.get(robot_id):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug(f"Robot {robot_id}: Task SIO Receiver stopped")
            del self._sio_receiver_tasks[robot_id]
        if robot_id in self._sio_receiver_queues:
            del self._sio_receiver_queues[robot_id]
        if self._sio.connected:
            # Only update start pose commands if del_robot is not called during disconnection
            await self.update_start_pose_commands()

    async def starter_changed(self, robot_id: int, pushed: bool):
        if not (robot := self._robots.get(robot_id)):
            return
        if not robot.virtual:
            await self._sio_ns.emit("starter_changed", (robot_id, pushed))
        if pushed:
            await self._sio_ns.emit("game_reset", robot_id)

    async def update_start_pose_commands(self):
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
            await self._sio_ns.emit("register_menu", {"name": "planner", "menu": menu.menu.dict()})

    async def reset(self):
        """
        Reset planner, context, robots and actions.
        """
        self._game_context.reset()
        self.update_cake_obstacles()
        self._actions = actions.action_classes.get(self._game_context.strategy, actions.Actions)()

        # Remove robots and add them again to reset all robots.
        robots = {robot_id: robot.virtual for robot_id, robot in self._robots.items()}
        for robot_id, _ in robots.items():
            await self.del_robot(robot_id)
        for robot_id, virtual in robots.items():
            await self.add_robot(robot_id, virtual)

    async def reset_controllers(self):
        new_controller = self._game_context.default_controller
        for robot_id, robot in self._robots.items():
            if robot.controller == new_controller:
                continue
            robot.controller = new_controller
            await self._sio_ns.emit("set_controller", (robot_id, new_controller.value))

    def update_cake_obstacles(self, robot_id: int = 0):
        robot_ids = self._robots.keys() if robot_id == 0 else [robot_id]
        for robot_id in robot_ids:
            obstacles = []
            for cake in self._game_context.cakes:
                if not cake.on_table:
                    continue
                if cake.robot and cake.robot.robot_id == robot_id:
                    continue
                cake.update_obstacle_properties(self._properties)
                obstacles.append(cake.obstacle.dict(exclude_defaults=True))
            self._shared_cake_obstacles[robot_id] = obstacles

    async def set_pose_start(self, robot_id: int, pose_start: models.Pose):
        """
        Set the start position of the robot for the next game.
        """
        await self._sio_ns.emit("pose_start", (robot_id, pose_start.dict()))

    def set_pose_current(self, robot_id: int, pose: models.Pose) -> None:
        """
        Set current pose of a robot.
        """
        if not (robot := self._robots.get(robot_id)):
            return
        robot.pose_current = models.Pose.parse_obj(pose)

    async def set_pose_reached(self, robot_id: int):
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
        await robot.set_pose_reached(True)

        if not self._game_context.playing:
            return

        await self.next_pose(robot_id)

    async def next_pose(self, robot_id: int):
        """
        Select the next pose for a robot.
        """
        if not (robot := self._robots.get(robot_id)):
            return

        # Get and set new pose
        new_pose_order = await robot.next_pose()

        # If no pose left in current action, get and set new action
        if not new_pose_order and (new_action := self.get_action(robot_id)):
            await robot.set_action(new_action)

    async def game_end(self, robot_id: int):
        self.cmd_stop()
        await self._sio_ns.emit("score", self._game_context.score)

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

    async def blocked(self, robot_id: int):
        """
        Function called when a robot cannot find a path to go to the current pose of the current action
        """
        if current_action := (robot := self._robots[robot_id]).action:
            if new_action := self.get_action(robot_id):
                await robot.set_action(new_action)
                await current_action.recycle(self)
                self._actions.append(current_action)

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

        obstacle = models.DynRoundObstacle(
            x=center.x,
            y=center.y,
            radius=radius
        )
        obstacle.create_bounding_box(bb_radius, self._properties.obstacle_bb_vertices)

        return obstacle

    def set_obstacles(self, robot_id: int, obstacles: list[models.Vertex]) -> None:
        """
        Store obstacles detected by a robot sent by Detector.
        Add bounding box and radius.
        """
        if not (robot := self._robots.get(robot_id)):
            return

        bb_radius = self._properties.obstacle_radius + self._properties.robot_width / 2

        table = self._game_context.table
        robot.obstacles = [
            self.create_dyn_obstacle(obstacle, bb_radius)
            for obstacle in obstacles
            if table.contains(obstacle, self._properties.obstacle_radius)
        ]

    @property
    def all_obstacles(self) -> models.DynObstacleList:
        obstacles = sum([robot.obstacles for robot in self._robots.values()], start=[])
        obstacles.extend([cake.obstacle for cake in self._game_context.cakes if cake.on_table])
        return obstacles

    async def send_obstacles(self):
        await self._sio_ns.emit("obstacles", [o.dict(exclude_defaults=True) for o in self.all_obstacles])

    async def command(self, cmd: str):
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
            await self._sio_ns.emit("config", schema)
            return

        if cmd == "game_wizard":
            self._game_wizard.start()
            return

        if not (cmd_func := getattr(self, f"cmd_{cmd}", None)):
            logger.warning(f"Unknown command: {cmd}")
            return

        await cmd_func()

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
            case "robot_width" | "obstacle_bb_vertices":
                self.update_cake_obstacles()

    async def cmd_play(self):
        """
        Play command from the menu.
        """
        if self._game_context.playing:
            return

        self._game_context.playing = True
        for robot_id in self._robots.keys():
            queue = self._sio_receiver_queues[robot_id]
            await queue.put(self.set_pose_reached(robot_id))

    async def cmd_stop(self):
        """
        Stop command from the menu.
        """
        self._game_context.playing = False

    async def cmd_next(self):
        """
        Next command from the menu.
        Ignored if current pose is not reached for all robots.
        """
        if self._game_context.playing:
            return

        # Check that pose_reached is set for all robots
        if not all([robot.pose_reached for robot in self._robots.values()]):
            return

        for robot_id in self._robots.keys():
            queue = self._sio_receiver_queues[robot_id]
            await queue.put(self.next_pose(robot_id))

    async def cmd_reset(self):
        """
        Reset command from the menu.
        """
        await self.reset()
        await self._sio_ns.emit("cmd_reset")

    async def cmd_choose_camp(self):
        """
        Choose camp command from the menu.
        Send camp wizard message.
        """
        await self._sio_ns.emit(
            "wizard",
            {
                "name": "Choose Camp",
                "type": "camp",
                "value": self._camp.color.name
            }
        )

    async def cmd_choose_strategy(self):
        """
        Choose strategy command from the menu.
        Send strategy wizard message.
        """
        await self._sio_ns.emit(
            "wizard",
            {
                "name": "Choose Strategy",
                "type": "choice_str",
                "choices": [e.name for e in Strategy],
                "value": self._game_context.strategy.name
            }
        )

    async def cmd_choose_avoidance(self):
        """
        Choose avoidance strategy command from the menu.
        Send avoidance strategy wizard message.
        """
        await self._sio_ns.emit(
            "wizard",
            {
                "name": "Choose Avoidance",
                "type": "choice_str",
                "choices": [e.name for e in AvoidanceStrategy],
                "value": self._game_context.avoidance_strategy.name
            }
        )

    async def cmd_choose_start_position(self, robot_id):
        """
        Choose start position command from the menu.
        Send start position wizard message.
        """
        await self._sio_ns.emit(
            "wizard",
            {
                "name": f"Choose Start Position {robot_id}",
                "type": "choice_integer",
                "choices": self._game_context.get_available_start_poses(),
                "value": self._start_positions.get(robot_id, robot_id),
                "robot_id": robot_id
            }
        )

    async def cmd_choose_table(self):
        """
        Choose table command from the menu.
        Send table wizard message.
        """
        await self._sio_ns.emit(
            "wizard",
            {
                "name": "Choose Table",
                "type": "choice_str",
                "choices": [e.name for e in TableEnum],
                "value": self._game_context._table.name
            }
        )

    async def wizard_response(self, message: dict[str, Any]):
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
                await self.reset()
                logger.info(f"Wizard: New camp: {self._camp.color.name}")
            case "Choose Strategy":
                new_strategy = Strategy[value]
                if self._game_context.strategy == new_strategy:
                    return
                self._game_context.strategy = new_strategy
                await self.reset()
                await self.reset_controllers()
                logger.info(f'Wizard: New strategy: {self._game_context.strategy.name}')
            case "Choose Avoidance":
                new_strategy = AvoidanceStrategy[value]
                if self._game_context.avoidance_strategy == new_strategy:
                    return
                self._game_context.avoidance_strategy = new_strategy
                await self.reset()
                logger.info(f'Wizard: New avoidance strategy: {self._game_context.avoidance_strategy.name}')
            case chose_start_pose if chose_start_pose.startswith("Choose Start Position"):
                if robot := self._robots.get(robot_id := message.get("robot_id")):
                    start_position = int(value)
                    self._start_positions[robot_id] = start_position
                    await robot.set_pose_start(self._game_context.get_start_pose(start_position).pose)
            case "Choose Table":
                new_table = TableEnum[value]
                if self._game_context.table == new_table:
                    return
                self._game_context.table = new_table
                self._shared_properties["table"] = new_table
                await self.reset()
                logger.info(f'Wizard: New table: {self._game_context._table.name}')
            case game_wizard_response if game_wizard_response.startswith("Game Wizard"):
                self._game_wizard.response(message)
            case wizard_test_response if wizard_test_response.startswith("Wizard Test"):
                logger.info(f"Wizard test response: {name} = {value}")
            case _:
                logger.warning(f"Wizard: Unknown type: {name}")

    async def cmd_wizard_test(self, cmd: str):
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
                await self._sio_ns.emit("score", 100)
                return
            case _:
                logger.warning(f"Wizard test unsupported: {cmd}")
                return

        await self._sio_ns.emit("wizard", message)

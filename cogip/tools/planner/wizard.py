from typing import Any, TYPE_CHECKING

from cogip.utils.asyncloop import AsyncLoop
from .avoidance.avoidance import AvoidanceStrategy
from .camp import Camp
from .context import GameContext
from .strategy import Strategy

if TYPE_CHECKING:
    from cogip.tools.planner.planner import Planner


class GameWizard:
    def __init__(self, planner: "Planner"):
        self.planner = planner
        self.game_context = GameContext()
        self.step = 0
        self.robot_index = 0
        self.started = False
        self.waiting_start_loop = AsyncLoop(
            "Waiting start thread",
            0.1,
            self.check_start,
            logger=True
        )

        self.steps = [
            (self.request_camp, self.response_camp),
            (self.request_start_pose, self.response_start_pose),
            (self.request_strategy, self.response_strategy),
            (self.request_avoidance, self.response_avoidance),
            (self.request_starter, self.response_starter),
            (self.request_wait, self.response_wait)
        ]

    def reset(self):
        self.step = 0
        self.robot_index = 0
        self.started = False

    async def start(self):
        self.reset()
        await self.next()

    async def next(self):
        self.step += 1
        if self.step <= len(self.steps):
            step_request, _ = self.steps[self.step - 1]
            await step_request()

    async def response(self, message: dict[str, Any]):
        _, step_response = self.steps[self.step - 1]
        await step_response(message)
        await self.next()

    async def request_camp(self):
        message = {
            "name": "Game Wizard: Choose Camp",
            "type": "camp",
            "value": self.planner._camp.color.name
        }
        await self.planner._sio_ns.emit("wizard", message)

    async def response_camp(self, message: dict[str, Any]):
        value = message["value"]
        self.planner._camp.color = Camp.Colors[value]
        await self.planner.reset()

    async def request_start_pose(self):
        if self.robot_index >= len(self.planner._robots):
            self.robot_index = 0
            await self.next()
            return

        robot_id = list(self.planner._robots.keys())[self.robot_index]

        message = {
            "name": f"Game Wizard: Choose Start Position {robot_id}",
            "type": "choice_integer",
            "choices": list(range(1, 6)),
            "value": self.planner._start_positions.get(robot_id, robot_id),
            "robot_id": robot_id
        }
        await self.planner._sio_ns.emit("wizard", message)

    async def response_start_pose(self, message: dict[str, Any]):
        value = message["value"]
        if robot := self.planner._robots.get(robot_id := message.get("robot_id")):
            start_position = int(value)
            self.planner._start_positions[robot_id] = start_position
            await robot.set_pose_start(self.game_context.get_start_pose(start_position).pose)

        if self.robot_index < len(self.planner._robots) - 1:
            self.step -= 1
            self.robot_index += 1
            return

    async def request_strategy(self):
        message = {
            "name": "Game Wizard: Choose Strategy",
            "type": "choice_str",
            "choices": [e.name for e in Strategy],
            "value": self.game_context.strategy.name
        }
        await self.planner._sio_ns.emit("wizard", message)

    async def response_strategy(self, message: dict[str, Any]):
        value = message["value"]
        new_strategy = Strategy[value]
        if self.game_context.strategy == new_strategy:
            return
        self.game_context.strategy = new_strategy
        self.planner._shared_properties["strategy"] = new_strategy
        await self.planner.reset()

    async def request_avoidance(self):
        message = {
            "name": "Game Wizard: Choose Avoidance",
            "type": "choice_str",
            "choices": [e.name for e in AvoidanceStrategy],
            "value": self.game_context.avoidance_strategy.name
        }
        await self.planner._sio_ns.emit("wizard", message)

    async def response_avoidance(self, message: dict[str, Any]):
        value = message["value"]
        new_strategy = AvoidanceStrategy[value]
        if self.game_context.avoidance_strategy == new_strategy:
            return
        self.game_context.avoidance_strategy = new_strategy
        self.planner._shared_properties["avoidance_strategy"] = new_strategy
        self.reset()

    async def request_starter(self):
        if self.robot_index >= len(self.planner._robots):
            self.waiting_start_loop.start()
            self.robot_index = 0
            await self.next()
            return

        robot_id, robot = list(self.planner._robots.items())[self.robot_index]
        if robot.starter.is_pressed:
            self.robot_index += 1
            self.step -= 1
            await self.next()
            return

        message = {
            "name": "Game Wizard: Starter Check",
            "type": "message",
            "value": f"Please insert starter in Robot {robot_id}",
            "robot_id": robot_id
        }
        await self.planner._sio_ns.emit("wizard", message)

    async def response_starter(self, message: dict[str, Any]):
        robot_id = message["robot_id"]
        robot = self.planner._robots[robot_id]
        if not robot.starter.is_pressed:
            self.step -= 1
            return

        if self.robot_index < len(self.planner._robots) - 1:
            self.step -= 1
            self.robot_index += 1
            return

        self.waiting_start_loop.start()

    async def request_wait(self):
        message = {
            "name": "Game Wizard: Waiting Start",
            "type": "message",
            "value": f"Remove starter{'s' if len(self.planner._robots) else ''} to start the game"
        }
        await self.planner._sio_ns.emit("wizard", message)

    async def response_wait(self, message: dict[str, Any]):
        if self.started:
            self.reset()
            return

        self.step -= 1

    async def check_start(self):
        if not all([not robot.starter.is_pressed for robot in self.planner._robots.values()]):
            return

        self.waiting_start_loop.exit = True
        self.started = True
        await self.planner._sio_ns.emit("close_wizard")
        await self.planner.reset()
        await self.planner._sio_ns.emit("game_start")
        await self.planner.cmd_play()

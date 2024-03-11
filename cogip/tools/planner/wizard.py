import asyncio
from typing import TYPE_CHECKING, Any

from cogip.utils.asyncloop import AsyncLoop
from . import actuators
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
        self.started = False
        self.waiting_start_loop = AsyncLoop(
            "Waiting start thread",
            0.1,
            self.check_start,
            logger=True,
        )

        self.steps = [
            (self.request_camp, self.response_camp),
            (self.request_start_pose, self.response_start_pose),
            (self.request_strategy, self.response_strategy),
            (self.request_avoidance, self.response_avoidance),
            (self.request_starter, self.response_starter),
            (self.request_wait, self.response_wait),
        ]

    def reset(self):
        self.step = 0
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
            "value": self.planner.camp.color.name,
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_camp(self, message: dict[str, Any]):
        value = message["value"]
        self.planner.camp.color = Camp.Colors[value]
        await self.planner.reset()

    async def request_start_pose(self):
        message = {
            "name": "Game Wizard: Choose Start Position",
            "type": "choice_integer",
            "choices": list(range(1, 4)),
            "value": self.planner.start_position,
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_start_pose(self, message: dict[str, Any]):
        value = message["value"]
        start_position = int(value)
        self.planner.start_position = start_position
        await self.planner.robot.set_pose_start(self.game_context.get_start_pose(start_position).pose)

    async def request_strategy(self):
        message = {
            "name": "Game Wizard: Choose Strategy",
            "type": "choice_str",
            "choices": [e.name for e in Strategy],
            "value": self.game_context.strategy.name,
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_strategy(self, message: dict[str, Any]):
        value = message["value"]
        new_strategy = Strategy[value]
        if self.game_context.strategy == new_strategy:
            return
        self.game_context.strategy = new_strategy
        self.planner.shared_properties["strategy"] = new_strategy
        await self.planner.reset()

    async def request_avoidance(self):
        message = {
            "name": "Game Wizard: Choose Avoidance",
            "type": "choice_str",
            "choices": [e.name for e in AvoidanceStrategy],
            "value": self.game_context.avoidance_strategy.name,
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_avoidance(self, message: dict[str, Any]):
        value = message["value"]
        new_strategy = AvoidanceStrategy[value]
        if self.game_context.avoidance_strategy == new_strategy:
            return
        self.game_context.avoidance_strategy = new_strategy
        self.planner.shared_properties["avoidance_strategy"] = new_strategy
        self.reset()

    async def request_starter(self):
        if self.planner.robot.starter.is_pressed:
            self.waiting_start_loop.start()
            await self.next()
            return

        message = {
            "name": "Game Wizard: Starter Check",
            "type": "message",
            "value": "Please insert starter in Robot",
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_starter(self, message: dict[str, Any]):
        if not self.planner.robot.starter.is_pressed:
            self.step -= 1
            return

        self.waiting_start_loop.start()

    async def request_wait(self):
        await actuators.led_on(self.planner)
        await actuators.central_arm_up(self.planner)
        await actuators.left_arm_up(self.planner)
        await actuators.right_arm_up(self.planner)
        await asyncio.sleep(1)
        await actuators.led_off(self.planner)

        message = {
            "name": "Game Wizard: Waiting Start",
            "type": "message",
            "value": "Remove starter to start the game",
        }
        await self.planner.sio_ns.emit("wizard", message)

    async def response_wait(self, message: dict[str, Any]):
        if self.started:
            self.reset()
            return

        self.step -= 1

    async def check_start(self):
        if self.planner.robot.starter.is_pressed:
            return

        self.waiting_start_loop.exit = True
        await self.waiting_start_loop.stop()
        self.started = True
        await self.planner.sio_ns.emit("close_wizard")
        await self.planner.reset()
        await self.planner.sio_ns.emit("game_start")
        await self.planner.cmd_play()

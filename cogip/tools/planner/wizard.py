from typing import Any

from . import planner
from .avoidance.avoidance import AvoidanceStrategy
from .camp import Camp
from .context import GameContext
from .strategy import Strategy


class GameWizard:
    def __init__(self, planner: "planner.Planner"):
        self.planner = planner
        self.game_context = GameContext()
        self.step = 0
        self.robot_index = 0

        self.steps = [
            (self.request_camp, self.response_camp),
            (self.request_start_pose, self.response_start_pose),
            (self.request_strategy, self.response_strategy),
            (self.request_avoidance, self.response_avoidance),
            # (self.request_starter, self.response_starter),
            (self.request_play, self.response_play)
        ]

    def reset(self):
        self.step = 0
        self.robot_index = 0

    def start(self):
        self.reset()
        self.next()

    def next(self):
        self.step += 1
        if self.step <= len(self.steps):
            step_request, _ = self.steps[self.step - 1]
            step_request()

    def response(self, message: dict[str, Any]):
        _, step_response = self.steps[self.step - 1]
        step_response(message)
        self.next()

    def request_camp(self):
        message = {
            "name": "Game Wizard: Choose Camp",
            "type": "camp",
            "value": self.planner._camp.color.name
        }
        self.planner._sio_ns.emit("wizard", message)

    def response_camp(self, message: dict[str, Any]):
        value = message["value"]
        self.planner._camp.color = Camp.Colors[value]
        self.planner.reset()

    def request_start_pose(self):
        if self.robot_index >= len(self.planner._robots):
            self.robot_index = 0
            self.next()
            return

        robot_id, robot = list(self.planner._robots.items())[self.robot_index]

        message = {
            "name": f"Game Wizard: Choose Start Position {robot_id}",
            "type": "choice_integer",
            "choices": list(range(1, 6)),
            "value": self.planner._start_positions.get(robot_id, robot_id),
            "robot_id": robot_id
        }
        self.planner._sio_ns.emit("wizard", message)

    def response_start_pose(self, message: dict[str, Any]):
        value = message["value"]
        if robot := self.planner._robots.get(robot_id := message.get("robot_id")):
            start_position = int(value)
            self.planner._start_positions[robot_id] = start_position
            robot.set_pose_start(self.game_context.get_start_pose(start_position))

        if self.robot_index < len(self.planner._robots) - 1:
            self.step -= 1
            self.robot_index += 1
            return

    def request_strategy(self):
        message = {
            "name": "Game Wizard: Choose Strategy",
            "type": "choice_str",
            "choices": [e.name for e in Strategy],
            "value": self.game_context.strategy.name
        }
        self.planner._sio_ns.emit("wizard", message)

    def response_strategy(self, message: dict[str, Any]):
        value = message["value"]
        new_strategy = Strategy[value]
        if self.game_context.strategy == new_strategy:
            return
        self.game_context.strategy = new_strategy
        self.planner.reset()
        self.planner.reset_controllers()

    def request_avoidance(self):
        message = {
            "name": "Game Wizard: Choose Avoidance",
            "type": "choice_str",
            "choices": [e.name for e in AvoidanceStrategy],
            "value": self.game_context.avoidance_strategy.name
        }
        self.planner._sio_ns.emit("wizard", message)

    def response_avoidance(self, message: dict[str, Any]):
        value = message["value"]
        new_strategy = AvoidanceStrategy[value]
        if self.game_context.avoidance_strategy == new_strategy:
            return
        self.game_context.avoidance_strategy = new_strategy
        self.reset()

    # def request_starter(self):
    #     # TODO
    #     pass

    # def response_start(self, message: dict[str, Any]):
    #     # TODO
    #     pass

    def request_play(self):
        message = {
            "name": "Game Wizard: Ready?",
            "type": "boolean",
            "value": False
        }
        self.planner._sio_ns.emit("wizard", message)

    def response_play(self, message: dict[str, Any]):
        ready = message["value"]
        if not ready:
            self.reset()
            return

        self.planner.reset()

        # TODO: wait for starter
        self.planner._sio_ns.emit("close_wizard")
        self.planner.reset()
        self.planner.cmd_play()

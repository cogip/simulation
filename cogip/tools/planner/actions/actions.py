import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, final

from .. import logger
from ..context import GameContext
from ..pose import Pose

if TYPE_CHECKING:
    from ..planner import Planner
    from ..robot import Robot


class Action:
    """
    This class represents an action of the game.
    It contains a list of Pose to reach in order.
    A function can be executed before the action starts and after it ends.
    """

    def __init__(self, name: str, planner: "Planner", actions: "Actions", interruptable: bool = True):
        self.name = name
        self.planner = planner
        self.actions = actions
        self.interruptable = interruptable
        self.game_context = GameContext()
        self.robot: "Robot" | None = None
        self.poses: list[Pose] = []
        self.before_action_func: Callable[[], Awaitable[None]] | None = None
        self.after_action_func: Callable[[], Awaitable[None]] | None = None
        self.recycled: bool = False

    def weight(self, robot: "Robot") -> float:
        """
        Weight of the action.
        It can be used to choose the next action to select.
        This is the generic implementation.
        """
        raise NotImplementedError

    @final
    async def act_before_action(self):
        """
        Function executed before the action starts.
        """
        if self.before_action_func:
            await self.before_action_func()

    @final
    async def act_after_action(self):
        """
        Function executed after the action ends.
        """
        if self.after_action_func:
            await self.after_action_func()

        # Re-enable all actions after a successful action
        for action in self.actions:
            action.recycled = False

    async def recycle(self):
        """
        Function called if the action is blocked and put back in the actions list
        """
        self.recycled = True


class WaitAction(Action):
    """
    Action used if no other action is available.
    Reset recycled attribute of all actions at the end.
    """

    def __init__(self, planner: "Planner", actions: "Actions"):
        super().__init__("Wait action", planner, actions)
        self.before_action_func = self.before_wait
        self.after_action_func = self.after_wait

    def weight(self, robot: "Robot") -> float:
        return 1

    async def before_wait(self):
        logger.debug(f"Robot {self.robot.robot_id}: WaitAction: before action")

    async def after_wait(self):
        logger.debug(f"Robot {self.robot.robot_id}: WaitAction: after action")
        await asyncio.sleep(2)

        for action in self.actions:
            action.recycled = False

        self.actions.append(WaitAction(self.planner, self.actions))


class Actions(list[Action]):
    """
    List of actions.
    Just inherits from list for now.
    """

    def __init__(self, planner: "Planner"):
        super().__init__()
        self.planner = planner
        self.game_context = GameContext()

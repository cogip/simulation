from collections.abc import Awaitable, Callable
from typing import final

from cogip.models.models import PathPose


class Pose(PathPose):
    """
    Pose class used in actions.
    A function can be executed before moving and an other once it is reached.
    """

    before_pose_func: Callable[[], Awaitable[None]] | None = None
    intermediate_pose_func: Callable[[], Awaitable[None]] | None = None
    after_pose_func: Callable[[], Awaitable[None]] | None = None

    @final
    async def act_before_pose(self):
        """
        Function executed before the robot starts moving.
        """
        if self.before_pose_func:
            await self.before_pose_func()

    @final
    async def act_intermediate_pose(self):
        """
        Function executed once an intermediate pose is reached.
        """
        if self.intermediate_pose_func:
            await self.intermediate_pose_func()

    @final
    async def act_after_pose(self):
        """
        Function executed once the pose is reached.
        """
        if self.after_pose_func:
            await self.after_pose_func()

    @property
    def path_pose(self) -> PathPose:
        """
        Convert the pose into its parent class.
        """
        return PathPose(**self.model_dump())

from typing import Callable, ClassVar

from pydantic import validator
import socketio

from cogip.models.models import PathPose
from cogip.tools import planner
from .camp import Camp


class Pose(PathPose):
    """
    Pose class used in actions.
    A function can be executed before moving and an other once it is reached.
    """
    before_pose_func: Callable[[socketio.ClientNamespace], None] = lambda planner: None
    after_pose_func: Callable[[socketio.ClientNamespace], None] = lambda planner: None

    def act_before_pose(self, planner: "planner.planner.Planner") -> None:
        """
        Function executed before the robot starts moving.

        Parameters:
            planner: the planner object to send it information or orders
        """
        self.before_pose_func(planner)

    def act_after_pose(self, planner: "planner.planner.Planner") -> None:
        """
        Function executed once the pose is reached.

        Parameters:
            planner: the planner object to send it information or orders
        """
        self.after_pose_func(planner)

    @property
    def path_pose(self) -> PathPose:
        """
        Convert the pose into its parent class.
        """
        return PathPose(**self.dict())


class AdaptedPose(Pose):
    """
    Like a Pose, but its values are automatically adapted to selected camp
    during initialization.
    So to define static positions in actions, we can use this class to set pose related
    to the default camp, and if the camp changes, the pose will be adapted on reset.
    """
    _camp: ClassVar[Camp] = Camp()

    class Config:
        underscore_attrs_are_private = True

    @validator('y')
    def adapt_y(cls, v, **kwargs):
        """
        Validator to adapt Y depending on the camp at initialization.
        """
        return Camp().adapt_y(v)

    @validator('O')
    def adapt_O(cls, v, **kwargs):
        """
        Validator to adapt the angle depending on the camp at initialization.
        """
        return Camp().adapt_angle(v)

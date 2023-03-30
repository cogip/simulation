from typing import Callable, ClassVar

from pydantic import validator
import socketio

from cogip.models.models import PathPose
from .camp import Camp


class Pose(PathPose):
    """
    Pose class used in actions.
    A function can be executed before moving and an other once it is reached.
    """
    before_pose_func: Callable[[socketio.ClientNamespace], None] = lambda sio: None
    after_pose_func: Callable[[socketio.ClientNamespace], None] = lambda sio: None

    def act_before_pose(self, sio: socketio.ClientNamespace) -> None:
        """
        Function executed before the robot starts moving.

        Parameters:
            sio: SocketIO client to emit message to the server
        """
        self.before_pose_func(sio)

    def act_after_pose(self, sio: socketio.ClientNamespace) -> None:
        """
        Function executed once the pose is reached.

        Parameters:
            sio: SocketIO client to emit message to the server
        """
        self.after_pose_func(sio)

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

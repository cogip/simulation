from cogip.models import models
from . import actions, context, pose, sio_events


class Robot:
    """
    Class representing a robot context.
    """
    def __init__(self, robot_id: int, sio: sio_events.SioEvents):
        self.robot_id = robot_id
        self.sio = sio
        self.game_context = context.GameContext()
        self.action: actions.Action | None = None
        self._pose_reached: bool = True
        self.pose_current: models.Pose | None = None
        self.pose_order: pose.Pose | None = None

    def set_pose_start(self, pose: pose.Pose):
        """
        Set the start pose.
        """
        self.action = None
        self.pose_current = pose.pose
        self.pose_order = pose
        self._pose_reached = True
        self.sio.emit("pose_start", (self.robot_id, self.pose_order.pose.dict()))
        self.pose_order.act_after_pose(self.sio)

    @property
    def pose_reached(self) -> bool:
        return self._pose_reached

    @pose_reached.setter
    def pose_reached(self, reached: bool = True):
        """
        Set pose reached.
        If reached, a new pose and new action is selected.
        """
        if reached and not self.pose_reached and self.pose_order:
            self.pose_order.act_after_pose(self.sio)
        self._pose_reached = reached
        self.pose_order = None
        if self.action and len(self.action.poses) == 0:
            self.action.act_after_action(self.sio)
            self.action = None

    def next_pose(self) -> pose.Pose | None:
        """
        Select next pose.
        Returns None if no more pose is available in the current action.
        """
        self._pose_reached = False
        if not self.action or len(self.action.poses) == 0:
            self.action = None
            return None

        self.pose_order = self.action.poses.pop(0)
        self.pose_order.act_before_pose(self.sio)
        self.sio.emit("pose_order", (self.robot_id, self.pose_order.path_pose.dict()))
        return self.pose_order

    def set_action(self, action: "actions.Action"):
        """
        Set current action.
        """
        self.action = action
        self.action.act_before_action(self.sio)
        self.next_pose()

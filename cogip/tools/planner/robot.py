from cogip.models import models
from cogip.tools import planner
from cogip.tools.copilot.controller import ControllerEnum
from . import actions, context, pose


class Robot:
    """
    Class representing a robot context.
    """
    def __init__(self, robot_id: int, planner: "planner.planner.Planner"):
        self.robot_id = robot_id
        self.planner = planner
        self.game_context = context.GameContext()
        self.action: actions.Action | None = None
        self._pose_reached: bool = True
        self.pose_current: models.Pose | None = None
        self.pose_order: pose.Pose | None = None
        self.avoidance_path: list[pose.Pose] = []
        self.last_avoidance_pose_current: models.Pose | None = None
        self.last_emitted_pose_order: models.PathPose | None = None
        self.controller: ControllerEnum = self.game_context.default_controller
        self.obstacles: list[models.Vertex] = []

    def set_pose_start(self, pose: pose.Pose):
        """
        Set the start pose.
        """
        self.action = None
        self.pose_current = pose.pose
        self.pose_order = pose
        self._pose_reached = True
        self.avoidance_path = []
        self.planner.set_pose_start(self.robot_id, self.pose_order)
        self.pose_order.act_after_pose(self.planner)

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
            self.pose_order.act_after_pose(self.planner)
        self._pose_reached = reached
        self.pose_order = None
        self.avoidance_path = []
        if self.action and len(self.action.poses) == 0:
            self.action.act_after_action(self.planner)
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
        self.pose_order.act_before_pose(self.planner)
        self.planner.set_pose_order(self.robot_id, self.pose_order)
        return self.pose_order

    def set_action(self, action: "actions.Action"):
        """
        Set current action.
        """
        self.action = action
        self.action.act_before_action(self.planner)
        self.next_pose()

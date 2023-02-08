from cogip.utils.singleton import Singleton
from .camp import Camp
from .pose import AdaptedPose, Pose
from .strategy import Strategy


class GameContext(metaclass=Singleton):
    """
    A class recording the current game context.
    """
    def __init__(self):
        self.camp = Camp()
        self._strategy = Strategy.Approval
        self.playing: bool = False
        self.score: int = 0

    @property
    def strategy(self) -> Strategy:
        """
        Selected strategy.
        """
        return self._strategy

    @strategy.setter
    def strategy(self, s: Strategy):
        self._strategy = s
        self.reset()

    def reset(self):
        """
        Reset the context.
        """
        self.playing = False
        self.score = 0

    @classmethod
    def get_start_pose(cls, n: int) -> Pose | None:
        """
        Define the possible start positions.
        """
        match n:
            case 1:
                return AdaptedPose(x=225, y=-775, O=0)
            case 2:
                return AdaptedPose(x=1875, y=-775, O=90)
            case 3:
                return AdaptedPose(x=2775, y=-275, O=180)
            case 4:
                return AdaptedPose(x=2775, y=775, O=180)
            case 5:
                return AdaptedPose(x=1125, y=775, O=-90)
            case _:
                return None

from typing import List, Tuple

from PySide6 import QtCore
from PySide6.QtCore import Signal as qtSignal


class DataProxy(QtCore.QObject):
    """DataProxy class

    Receive points from the Lidar, store them et send them to the data model.

    Attributes:
        update_data: Qt signal emitted when new points are available
    """

    update_data: qtSignal = qtSignal()

    def __init__(
            self,
            angle_values: List[int],
            distance_values: List[int],
            intensity_values: List[int]):
        """Class constructor

        Arguments:
            angle_values: angle list to update
            distance_values: distance list to update
            intensity_values: intensity list to update
        """
        super().__init__()
        self.angle_values = angle_values
        self.distance_values = distance_values
        self.intensity_values = intensity_values
        self.filter = 0

    def set_filter(self, filter: int):
        """
        Qt Slot

        Set filter.

        Arguments:
            filter: new filter
        """
        self.filter = filter

    def filter_distance(self, distance: int, intensity: int) -> int:
        """
        Compute the filtered distance based on current raw distance, intensity and filter.

        Arguments:
            distance: current raw distance
            intensity: current intensity
        """
        if self.filter == 0:
            return distance
        if intensity == 0:
            return self.filter
        if 0 < distance <= self.filter:
            return distance
        return self.filter

    def new_data(self, points: List[Tuple[float, int, int]]) -> None:
        """
        Get new list of points.

        Arguments:
            points: new points
        """
        for i, (angle, distance, intensity) in enumerate(points):
            self.angle_values[i] = angle
            self.distance_values[i] = self.filter_distance(distance, intensity)
            self.intensity_values[i] = intensity
            self.update_data.emit()

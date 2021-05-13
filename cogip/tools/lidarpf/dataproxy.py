from typing import List

from pydantic import BaseModel

from PySide2 import QtCore
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot


class LidarData(BaseModel):
    """LidarData class

    Represents data provided by the firmware's shell

    Attributes:
        distances: distance values
        intensities: intensity values
    """
    distances: List[int]
    intensities: List[int]


class DataProxy(QtCore.QObject):
    """DataProxy class

    Receive data from to firmware, transform them et send them to the data model.

    Attributes:
        update_data: Qt signal emitted when new data are available
    """

    update_data: qtSignal = qtSignal()

    def __init__(
            self,
            distance_values: List[int],
            intensity_values: List[int]):
        """Class constructor

        Arguments:
            distance_values: distance list to update
            intensity_values: intensity list to update
        """
        super().__init__()
        self.distance_values = distance_values
        self.intensity_values = intensity_values

    @qtSlot()
    def new_data(self, data: LidarData) -> None:
        """
        Get new data and store them

        Arguments:
            data: new data to store
        """
        for i in range(360):
            self.distance_values[i] = data.distances[i]
            self.intensity_values[i] = data.intensities[i]

        self.update_data.emit()

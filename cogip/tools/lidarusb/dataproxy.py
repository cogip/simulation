import ctypes
from typing import List

from PySide2 import QtCore
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot


class DoubleByte(ctypes.Structure):
    """
    Store a 2-byte value represented by a low and a high byte.

    Attributes:
        low: low byte
        high: high byte
        value: give the computed value
    """
    _fields_ = [
        ('low', ctypes.c_ubyte),
        ('high', ctypes.c_ubyte),
    ]

    @property
    def value(self) -> int:
        return (self.high << 8) + self.low


class OffsetStruct(ctypes.Structure):
    """
    Store an offset data for one angle, composed by the distance and the intensity values.

    Attributes:
        dist: distance value
        intensity: intensity value
    """

    _fields_ = [
        ('_intensity', DoubleByte),
        ('_dist', DoubleByte),
        ('reserved', DoubleByte)
    ]

    @property
    def dist(self) -> int:
        return self._dist.value

    @property
    def intensity(self) -> int:
        return self._intensity.value


class FrameData(ctypes.Structure):
    """
    Store an frame composed of 6 offset data.

    Attributes:
        sync: start byte
        index: the first angle contained in the frame
        offsets: array of 6 [offsets][cogip.tools.lidarusb.dataproxy.OffsetStruct]
        checksum: 2 bytes to detect corrupted frames
    """

    _fields_ = [
        ('sync', ctypes.c_ubyte),
        ('_index', ctypes.c_ubyte),
        ('rpm', DoubleByte),
        ('offsets', OffsetStruct * 6),
        ('checksum', DoubleByte)
    ]

    @property
    def index(self) -> int:
        return self._index - 0xA0


class DataProxy(QtCore.QObject):
    """DataProxy class

    Receive data from the serial port, transform them et send them to the data model.

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
        self.filter = 0

    @qtSlot(int)
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

    @qtSlot(bytes)
    def new_data(self, frame_bytes: bytes) -> None:
        """
        Get new frame and store them

        Arguments:
            frame_bytes: new frame
        """
        frame_data = FrameData.from_buffer_copy(frame_bytes)

        for i in range(6):
            angle = frame_data.index + i
            distance = frame_data.offset[i].dist
            intensity = frame_data.offset[i].intensity
            self.distance_values[angle] = self.filter_distance(distance, intensity)
            self.intensity_values[angle] = intensity

        # Update chart (the full chart at once when all frames are updated)
        if frame_data.index == 59:
            self.update_data.emit()

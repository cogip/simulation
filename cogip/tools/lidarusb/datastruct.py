"""
This package contains classes/structures used to store data provided by the Lidar.
"""

import ctypes
from typing import List

from PySide2 import QtCore
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
        offsets: array of 6 [offsets][cogip.tools.lidarusb.datastruct.OffsetStruct]
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


class LidarData(QtCore.QObject):
    """
    Store an frame composed of 6 offset data.

    Attributes:
        frames: array of 60 [frames][cogip.tools.lidarusb.datastruct.FrameData] representing 360 angles
        filter_value: value used to filter the distance value
    """

    frames: List[FrameData] = [None]*60
    filter_value: int = 500

    def set_frame(self, offset: int, frame_data: FrameData) -> None:
        """
        Set the frame the specified offset.

        Arguments:
            offset: identify the frame to be updated
            frame_data: the frame data
        """
        self.frames[offset] = frame_data

    def distance(self, angle: int) -> int:
        """
        Return the distance filtered and unfiltered (if `filter_value == 0`)
        for the specified angle.

        Arguments:
            angle: select the distance to return
        """
        (frame, offset) = divmod(angle, 6)
        if (frame > len(self.frames) - 1) or not self.frames[frame]:
            return None
        distance = self.frames[frame].offsets[offset].dist
        if self.filter_value == 0:
            return distance
        if self.intensity(angle) == 0:
            return self.filter_value
        if 0 < distance <= self.filter_value:
            return distance
        return self.filter_value

    def intensity(self, angle) -> int:
        """
        Return the  intensity for the specified angle.

        Arguments:
            angle: select the intensity to return
        """
        (frame, offset) = divmod(angle, 6)
        if (frame > len(self.frames) - 1) or not self.frames[frame]:
            return None
        return self.frames[frame].offsets[offset].intensity

    @qtSlot(int)
    def set_filter_value(self, value: int) -> None:
        """
        QtSlot

        Set the filter value.

        Arguments:
            value: new filter value
        """
        self.filter_value = value

    def get_distance_points(self) -> List[QtCore.QPointF]:
        """
        Return a list of the 360 distance values to update the chart.
        """
        return [QtCore.QPointF(i, self.distance(i) or 0) for i in range(360)]

    def get_intensity_points(self) -> List[QtCore.QPointF]:
        """
        Return a list of the 360 intensity values to update the chart.
        """
        return [QtCore.QPointF(i, self.intensity(i) or 0) for i in range(360)]

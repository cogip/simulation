import math
import time

from more_itertools import consecutive_groups
from PySide6 import QtCore
from PySide6.QtCore import Signal as qtSignal
import ydlidar


class Lidar(QtCore.QObject):
    """
    Handle the Lidar device (YDLidar G2), start and stop the Lidar,
    read, filter and send data.
    It runs in its own thread.

    Attributes:
        signal_new_data:
            Qt signal emitted when a new frame is available
    """
    signal_new_data: qtSignal = qtSignal(bytes)

    def __init__(self):
        """
        Class constructor.

        Discover Lidar serial port, set Lidar options.
        """
        super().__init__()
        self._exiting = False
        self._intensity_threshold = 0
        ydlidar.os_init()
        for _, value in ydlidar.lidarPortList().items():
            port = value
        self._laser = ydlidar.CYdLidar()
        self._laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
        self._laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 230400)
        self._laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
        self._laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
        self._laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)
        self._laser.setlidaropt(ydlidar.LidarPropSampleRate, 5)
        self._laser.setlidaropt(ydlidar.LidarPropIntenstiy, True)
        self._laser.setlidaropt(ydlidar.LidarPropScanFrequency, 5.0)
        self._laser.setlidaropt(ydlidar.LidarPropMaxRange, 16)
        self._laser.setlidaropt(ydlidar.LidarPropMinRange, 0.12)
        self._laser.setlidaropt(ydlidar.LidarPropInverted, False)  # clockwise (default)
        self._laser.setlidaropt(ydlidar.LidarPropFixedResolution, False)

    def quit(self):
        """
        Request to exit the thread as soon as possible.
        """
        self._exiting = True

    def set_intensity_threshold(self, threshold: int):
        """
        Set new intensity threshold.
        """
        self._intensity_threshold = threshold

    def process_points(self):
        """
        Read Lidar data, filter and send them to display.
        This is the thread loop.
        """
        self._laser.initialize()
        self._laser.turnOn()

        scan = ydlidar.LaserScan()
        while not self._exiting and ydlidar.os_isOk():
            ret = self._laser.doProcessSimple(scan)
            if ret:
                tmp_distances = [[] for _ in range(360)]
                tmp_intensities = [[] for _ in range(360)]
                result = []

                # Build a list of points for each integer degree
                for point in scan.points:
                    angle = round(math.degrees(point.angle))
                    if -180 <= angle < 180 and point.range > 0.0:
                        tmp_distances[angle + 180].append(point.range)
                        tmp_intensities[angle + 180].append(point.intensity)

                # Compute mean of points list for each degree.
                empty_angles = []
                for angle, (distances, intensities) in enumerate(zip(tmp_distances, tmp_intensities)):
                    distance = 4500
                    intensity = 1024
                    if size := len(distances):
                        distance = round(sum(distances) * 1000 / size)
                        intensity = int(sum(intensities) / size)
                    else:
                        empty_angles.append(angle)

                    result.append((
                        angle - 180,
                        distance,
                        intensity
                    ))

                # If a degree has no valid point and is isolated (no other empty angle before and after)
                # it is probably a bad value, so set it to the mean of surrounding degrees.
                for group in consecutive_groups(empty_angles):
                    g = list(group)
                    if len(g) == 1:
                        index = g[0]
                        isolated = result[index]
                        before = result[(index - 1) % 360]
                        after = result[(index + 1) % 360]
                        result[index] = (
                            isolated[0],
                            round((before[1] + after[1]) / 2),
                            round((before[2] + after[2]) / 2),
                        )

                self.signal_new_data.emit(result)
            else:
                print("Failed to get Lidar Data")

            time.sleep(0.5)

        self._laser.turnOff()
        self._laser.disconnecting()

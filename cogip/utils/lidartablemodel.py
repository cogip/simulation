from typing import List

from PySide6 import QtCore, QtWidgets, QtGui


class LidarTableModel(QtCore.QAbstractTableModel):
    """
    Model class providing access to data to update the table view.
    """

    headers = ["Angle", "Distance", "Intensity"]

    def __init__(
            self,
            angle_values: List[float],
            distance_values: List[int],
            intensity_values: List[int],
            distance_color: QtGui.QColor,
            intensity_color: QtGui.QColor,
            nb_angles: int = 360):
        """Class constructor

        Arguments:
            angle_values: angle values list
            distance_values: distance values list
            intensity_values: intensity values list
            distance_color: distance color
            intensity_color: intensity color
            nb_angles: number of angles
        """
        super().__init__()
        self.angle_values = angle_values
        self.distance_values = distance_values
        self.intensity_values = intensity_values
        self.distance_color = distance_color
        self.intensity_color = intensity_color
        self.nb_angles = nb_angles

    def rowCount(self, parent):
        return self.nb_angles

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        row, column = index.row(), index.column()

        if role == QtCore.Qt.BackgroundRole:
            if column == 0:
                return QtGui.QColor("lightgray")
            if column == 1:
                return self.distance_color
            if column == 2:
                return self.intensity_color
            return None

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignRight

        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return self.angle_values[row]
            if column == 1:
                return self.distance_values[row]
            if column == 2:
                return self.intensity_values[row]
            return None

        return None

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.BackgroundRole:
            return QtGui.QColor("lightgray")

        if role == QtCore.Qt.FontRole:
            font = QtWidgets.QApplication.font()
            font.setPointSize(font.pointSize() - 2)
            return font

        if role != QtCore.Qt.DisplayRole or orientation != QtCore.Qt.Horizontal:
            return None
        return self.headers[section]

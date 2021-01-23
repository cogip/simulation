from PySide2 import QtCore, QtWidgets, QtGui

from cogip.tools.lidarusb import datastruct


class TableModel(QtCore.QAbstractTableModel):
    """
    Model class providing access to data to update the table view.
    """

    headers = ["Angle", "Distance", "Intensity"]

    def __init__(
            self,
            lidar_data: datastruct.LidarData,
            distance_color: QtGui.QColor,
            intensity_color: QtGui.QColor):
        super().__init__()
        self.lidar_data = lidar_data
        self.distance_color = distance_color
        self.intensity_color = intensity_color

    def rowCount(self, parent):
        return 360

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
                return row
            if column == 1:
                return self.lidar_data.distance(row)
            if column == 2:
                return self.lidar_data.intensity(row)
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

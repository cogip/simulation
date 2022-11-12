from PySide6 import QtWidgets

from cogip.widgets.lidarview import LidarView


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, lidar_view: LidarView, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Lidar USB Viewer')

        self.lidar_view = lidar_view
        self.setCentralWidget(self.lidar_view)

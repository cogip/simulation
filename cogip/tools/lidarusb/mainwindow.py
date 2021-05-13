from PySide2 import QtGui, QtWidgets

from cogip.widgets.lidarview import LidarView


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, lidar_view: LidarView, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Lidar USB Viewer')

        self.lidar_view = lidar_view
        self.setCentralWidget(self.lidar_view)

        # Toolbars
        toolbar = self.addToolBar('Control')

        # Start action
        self.start_action = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("media-playback-start"),
            'Start',
            self
        )
        self.start_action.setStatusTip('Start Lidar')
        toolbar.addAction(self.start_action)

        # Pause action
        self.pause_action = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("media-playback-pause"),
            'Pause',
            self
        )
        self.pause_action.setStatusTip('Pause Lidar')
        toolbar.addAction(self.pause_action)

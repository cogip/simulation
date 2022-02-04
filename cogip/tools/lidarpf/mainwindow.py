from PySide6 import QtGui, QtWidgets

from cogip.widgets.lidarview import LidarView


class MainWindow(QtWidgets.QMainWindow):
    """MainWindow class

    Build the main window.
    """

    def __init__(self, lidar_view: LidarView, *args, **kwargs):
        """Class constructor

        Arguments:
            lidar_view: Lidar view widget
        """
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Lidar Test Platform Viewer')

        self.lidar_view = lidar_view
        self.setCentralWidget(self.lidar_view)

        # Toolbars
        toolbar = self.addToolBar('Control')

        # Start action
        self.start_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("media-playback-start"),
            'Start',
            self
        )
        self.start_action.setStatusTip('Start Lidar')
        toolbar.addAction(self.start_action)

        # Pause action
        self.pause_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("media-playback-pause"),
            'Pause',
            self
        )
        self.pause_action.setStatusTip('Pause Lidar')
        toolbar.addAction(self.pause_action)

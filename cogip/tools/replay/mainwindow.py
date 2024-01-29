from functools import partial
from pathlib import Path
from typing import Dict, Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from cogip.models import RobotState
from cogip.widgets.chartsview import ChartsView
from cogip.widgets.gameview import GameView


class MainWindow(QtWidgets.QMainWindow):
    """MainWindow class

    Build the main window of the game replay tool.

    It contains:

      - a menu bar,
      - a tool bar with buttons to load a trace file,
      - a status bar with robot position,
      - a slider with buttons to start/stop playback

    Attributes:
        signal_new_robot_state: Qt signal emitted on robot state update
        rate: number of milliseconds between two states during automatic playback
    """
    signal_new_robot_state: qtSignal = qtSignal(RobotState)
    rate: int = 60

    def __init__(self, trace: Optional[Path] = None, *args, **kwargs):
        """
        """
        super(MainWindow, self).__init__(*args, **kwargs)
        self.states = []
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.increment)

        self.menu_widgets: Dict[str, QtWidgets.QWidget] = {}

        self.setWindowTitle('COGIP Replay')

        self.central_widget = QtWidgets.QWidget()
        self.central_layout = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        view_menu = menubar.addMenu('&View')

        # Toolbars
        file_toolbar = self.addToolBar('File')

        # Status bar
        status_bar = self.statusBar()

        cycle_label = QtWidgets.QLabel("Cycle:")
        self.cycle_text = QtWidgets.QLabel()
        self.cycle_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.cycle_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        status_bar.addPermanentWidget(cycle_label, 0)
        status_bar.addPermanentWidget(self.cycle_text, 0)

        pos_x_label = QtWidgets.QLabel("X:")
        self.pos_x_text = QtWidgets.QLabel()
        self.pos_x_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.pos_x_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        status_bar.addPermanentWidget(pos_x_label, 0)
        status_bar.addPermanentWidget(self.pos_x_text, 0)

        pos_y_label = QtWidgets.QLabel("Y:")
        self.pos_y_text = QtWidgets.QLabel()
        self.pos_y_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.pos_y_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        status_bar.addPermanentWidget(pos_y_label, 0)
        status_bar.addPermanentWidget(self.pos_y_text, 0)

        pos_angle_label = QtWidgets.QLabel("Angle:")
        self.pos_angle_text = QtWidgets.QLabel()
        self.pos_angle_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.pos_angle_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        status_bar.addPermanentWidget(pos_angle_label, 0)
        status_bar.addPermanentWidget(self.pos_angle_text, 0)

        # Actions
        # Icons: https://commons.wikimedia.org/wiki/GNOME_Desktop_icons

        # Exit action
        self.exit_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("application-exit"),
            'Exit',
            self
        )
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(self.close)
        file_menu.addAction(self.exit_action)
        file_toolbar.addAction(self.exit_action)

        # Add obstacle action
        self.open_trace_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-open"),
            'Open trace',
            self
        )
        self.open_trace_action.setShortcut('Ctrl+O')
        self.open_trace_action.setStatusTip('Open trace')
        self.open_trace_action.triggered.connect(self.open_trace)
        file_menu.addAction(self.open_trace_action)
        file_toolbar.addAction(self.open_trace_action)

        # GameView widget
        self.game_view = GameView()
        self.central_layout.addWidget(self.game_view, stretch=100)

        # Slider widget
        slider_widget = QtWidgets.QWidget()
        slider_layout = QtWidgets.QHBoxLayout(slider_widget)
        slider_widget.setLayout(slider_layout)
        self.central_layout.addWidget(slider_widget, stretch=1)

        self.play_button = QtWidgets.QPushButton()
        self.play_button.setIcon(QtGui.QIcon.fromTheme("media-playback-start"))
        self.play_button.setStatusTip('Play')
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.play)
        slider_layout.addWidget(self.play_button)

        self.pause_button = QtWidgets.QPushButton()
        self.pause_button.setIcon(QtGui.QIcon.fromTheme("media-playback-pause"))
        self.pause_button.setStatusTip('Pause')
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause)
        slider_layout.addWidget(self.pause_button)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, minimum=0, maximum=100, value=00)
        self.slider.setMinimum(0)
        self.slider.setValue(0)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.slider_changed)
        self.slider.sliderMoved.connect(self.slider_moved)
        slider_layout.addWidget(self.slider)

        # Charts widget
        self.charts_view = ChartsView(self)

        # Add view action
        self.view_charts_action = QtGui.QAction('Calibration Charts', self)
        self.view_charts_action.setStatusTip('Display/Hide calibration charts')
        self.view_charts_action.setCheckable(True)
        self.view_charts_action.toggled.connect(self.charts_toggled)
        self.charts_view.closed.connect(partial(self.view_charts_action.setChecked, False))
        view_menu.addAction(self.view_charts_action)

    @qtSlot(bool)
    def charts_toggled(self, checked: bool):
        """
        Qt Slot

        Show/hide the calibration charts.

        Arguments:
            checked: Show action has checked or unchecked
        """
        if checked:
            self.charts_view.show()
            self.charts_view.raise_()
            self.charts_view.activateWindow()
        else:
            self.charts_view.close()

    @qtSlot(RobotState)
    def new_robot_state(self, state: RobotState):
        """
        Qt Slot

        Update robot position information in the status bar.

        Arguments:
            state: Robot state
        """
        self.cycle_text.setText(f"{state.cycle or 0:>#6d}")
        self.pos_x_text.setText(f"{state.pose_current.x:> #6.2f}")
        self.pos_y_text.setText(f"{state.pose_current.y:> #6.2f}")
        self.pos_angle_text.setText(f"{state.pose_current.O:> #4.2f}")

    @qtSlot()
    def open_trace(self):
        """
        Qt Slot

        Open a file dialog to select a trace file.
        """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select file to load trace",
            dir="",
            filter="Text files (*.txt)",
            # Workaround a know Qt bug
            options=QtWidgets.QFileDialog.DontUseNativeDialog
        )
        if filename:
            self.load_trace(Path(filename))

    @qtSlot()
    def load_trace(self, trace_file: Path):
        """
        Qt Slot

        Load a trace file.
        """
        self.pause()
        with trace_file.open() as fd:
            lines = fd.readlines()
        self.states = [RobotState.model_validate_json(line) for line in lines]
        self.slider.setValue(0)
        self.slider.setMaximum(len(self.states) - 1)
        self.slider.setEnabled(True)
        self.slider_changed()

    @qtSlot()
    def play(self):
        """
        Qt Slot

        Start automatic playback.
        """
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.timer.start(self.rate)

    @qtSlot()
    def pause(self):
        """
        Qt Slot

        Stop automatic playback.
        """
        self.timer.stop()
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)

    @qtSlot()
    def slider_changed(self):
        """
        Qt Slot

        Send robot state update when the current index changes,
        ie when the slider moves, automatically or manually
        """
        self.signal_new_robot_state.emit(self.states[self.slider.value()])

    @qtSlot()
    def slider_moved(self):
        """
        Qt Slot

        Stop automatic playback when the slider is moved manually.
        """
        self.pause()

    def increment(self):
        """
        Jump to the next state.
        """
        self.slider.setValue(self.slider.value() + 1)

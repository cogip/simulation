from functools import partial
import json
from pathlib import Path
import re
from typing import Dict, Optional, List, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from cogip.widgets.chartsview import ChartsView
from cogip.widgets.dashboard import Dashboard
from cogip.widgets.gameview import GameView
from cogip.widgets.help import HelpCameraControlDialog
from cogip.models import Pose, ShellMenu, RobotState


class MainWindow(QtWidgets.QMainWindow):
    """MainWindow class

    Build the main window of the monitor.

    It contains:

      - a menu bar,
      - a tool bar with buttons to add/load/save obstacles,
      - a status bar with robot position and mode,
      - a menu with commands available in the current firmware shell menu,
      - a console recording the firmware output.

    Attributes:
        signal_send_command: Qt signal to send a command to the firmware
        signal_add_obstacle: Qt signal to add an obstacle
        signal_load_obstacles: Qt signal to load obstacles
        signal_save_obstacles: Qt signal to save obstacles
        signal_load_cake_layers: Qt signal to load cake layers
        signal_save_cake_layers: Qt signal to save cake layers
    """

    signal_send_command: qtSignal = qtSignal(str)
    signal_add_obstacle: qtSignal = qtSignal()
    signal_load_obstacles: qtSignal = qtSignal(Path)
    signal_save_obstacles: qtSignal = qtSignal(Path)
    signal_load_cake_layers: qtSignal = qtSignal(Path)
    signal_save_cake_layers: qtSignal = qtSignal(Path)

    def __init__(self, url: str, *args, **kwargs):
        """
        Class constructor.

        Arguments:
            url: URL of the copilot web server
        """
        super(MainWindow, self).__init__(*args, **kwargs)

        self.menu_widgets: Dict[str, QtWidgets.QWidget] = {}

        self.setWindowTitle('COGIP Monitor')

        self.central_widget = QtWidgets.QWidget()
        self.central_layout = QtWidgets.QHBoxLayout()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        obstacles_menu = menubar.addMenu('&Obstacles')
        cake_layers_menu = menubar.addMenu('&Cake Layers')
        view_menu = menubar.addMenu('&View')
        help_menu = menubar.addMenu('&Help')

        # Toolbars
        file_toolbar = self.addToolBar('File')
        file_toolbar.setObjectName("File Toolbar")
        obstacles_toolbar = self.addToolBar('Obstacles')
        obstacles_toolbar.setObjectName("Obstacles Toolbar")

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

        pos_mode_label = QtWidgets.QLabel("Mode:")
        self.pos_mode_text = QtWidgets.QLabel()
        self.pos_mode_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.pos_mode_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        status_bar.addPermanentWidget(pos_mode_label, 0)
        status_bar.addPermanentWidget(self.pos_mode_text, 0)

        self.connected_label = QtWidgets.QLabel("Disconnected")
        status_bar.addPermanentWidget(self.connected_label, 0)

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
        self.add_obstacle_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("list-add"),
            'Add obstacle',
            self
        )
        self.add_obstacle_action.setShortcut('Ctrl+A')
        self.add_obstacle_action.setStatusTip('Add obstacle')
        self.add_obstacle_action.triggered.connect(self.add_obstacle)
        obstacles_menu.addAction(self.add_obstacle_action)
        obstacles_toolbar.addAction(self.add_obstacle_action)

        # Open obstacles action
        self.load_obstacles_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-open"),
            'Load obstacles',
            self
        )
        self.load_obstacles_action.setShortcut('Ctrl+O')
        self.load_obstacles_action.setStatusTip('Load obstacles')
        self.load_obstacles_action.triggered.connect(self.load_obstacles)
        obstacles_menu.addAction(self.load_obstacles_action)
        obstacles_toolbar.addAction(self.load_obstacles_action)

        # Save obstacles action
        self.save_obstacles_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-save"),
            'Save obstacles',
            self
        )
        self.save_obstacles_action.setShortcut('Ctrl+S')
        self.save_obstacles_action.setStatusTip('Save obstacles')
        self.save_obstacles_action.triggered.connect(self.save_obstacles)
        obstacles_menu.addAction(self.save_obstacles_action)
        obstacles_toolbar.addAction(self.save_obstacles_action)

        # Open cake layers action
        self.load_cake_layers_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-open"),
            'Load cake layers',
            self
        )
        self.load_cake_layers_action.setStatusTip('Load cake layers')
        self.load_cake_layers_action.triggered.connect(self.load_cake_layers)
        cake_layers_menu.addAction(self.load_cake_layers_action)

        # Save cake layers action
        self.save_cake_layers_action = QtGui.QAction(
            QtGui.QIcon.fromTheme("document-save"),
            'Save cake layers',
            self
        )
        self.save_cake_layers_action.setStatusTip('Save cake layers')
        self.save_cake_layers_action.triggered.connect(self.save_cake_layers)
        cake_layers_menu.addAction(self.save_cake_layers_action)

        # Console
        dock = QtWidgets.QDockWidget("Console")
        dock.setObjectName("Console")
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        dock.setWidget(self.log_text)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        file_menu.addAction(dock.toggleViewAction())
        obstacles_menu.addAction(dock.toggleViewAction())

        # Shell menu
        self.current_menu: Optional[str] = None

        self.menu_staked_widget = QtWidgets.QStackedWidget()
        self.central_layout.insertWidget(0, self.menu_staked_widget, 1)

        # Set a empty menu to allocate some space in the UI
        empty_menu_widget = QtWidgets.QStackedWidget()
        empty_menu_layout = QtWidgets.QVBoxLayout()
        empty_menu_widget.setLayout(empty_menu_layout)
        empty_menu_title = QtWidgets.QLabel("No menu loaded")
        empty_menu_title.setTextFormat(QtCore.Qt.RichText)
        empty_menu_title.setAlignment(QtCore.Qt.AlignHCenter)
        empty_menu_title.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        empty_menu_title.setStyleSheet("font-weight: bold; color: blue")
        empty_menu_layout.addWidget(empty_menu_title)
        empty_menu_layout.addStretch()
        self.menu_staked_widget.addWidget(empty_menu_widget)

        # GameView widget
        self.game_view = GameView()
        self.central_layout.insertWidget(1, self.game_view, 10)

        # Charts widget
        self.charts_view = ChartsView(self)

        # Dashboard widget
        self.dashboard = Dashboard(url, self)

        # Help controls widget
        self.help_camera_control = HelpCameraControlDialog(self)

        # Add view action
        self.view_charts_action = QtGui.QAction('Calibration Charts', self)
        self.view_charts_action.setStatusTip('Display/Hide calibration charts')
        self.view_charts_action.setCheckable(True)
        self.view_charts_action.toggled.connect(self.charts_toggled)
        self.charts_view.closed.connect(partial(self.view_charts_action.setChecked, False))
        view_menu.addAction(self.view_charts_action)

        self.view_dashboard_action = QtGui.QAction('Dashboard', self)
        self.view_dashboard_action.setStatusTip('Display/Hide dashboard')
        self.view_dashboard_action.setCheckable(True)
        self.view_dashboard_action.toggled.connect(self.dashboard_toggled)
        self.dashboard.closed.connect(partial(self.view_dashboard_action.setChecked, False))
        view_menu.addAction(self.view_dashboard_action)

        # Add help action
        self.help_camera_control_action = QtGui.QAction('Camera control', self)
        self.help_camera_control_action.setStatusTip('Display camera control help')
        self.help_camera_control_action.triggered.connect(self.display_help_camera_control)
        self.dashboard.closed.connect(partial(self.help_camera_control_action.setChecked, False))
        help_menu.addAction(self.help_camera_control_action)

        self.readSettings()

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

    @qtSlot(bool)
    def dashboard_toggled(self, checked: bool):
        """
        Qt Slot

        Show/hide the dashboard.

        Arguments:
            checked: Show action was checked or unchecked
        """
        if checked:
            self.dashboard.show()
            self.dashboard.raise_()
            self.dashboard.activateWindow()
        else:
            self.dashboard.close()

    @qtSlot(Pose)
    def new_robot_pose(self, pose: Pose):
        """
        Qt Slot

        Update robot position information in the status bar.

        Arguments:
            pose: Robot pose
        """
        self.pos_x_text.setText(f"{pose.x:> #6.2f}")
        self.pos_y_text.setText(f"{pose.y:> #6.2f}")
        self.pos_angle_text.setText(f"{pose.O:> #4.2f}")

    @qtSlot(RobotState)
    def new_robot_state(self, state: RobotState):
        """
        Qt Slot

        Update robot state information in the status bar.

        Arguments:
            state: Robot state
        """
        self.pos_mode_text.setText(state.mode.name)
        self.cycle_text.setText(f"{state.cycle or 0:>#6d}")

    @qtSlot(ShellMenu)
    def load_menu(self, new_menu: ShellMenu):
        """
        Qt Slot

        Display the new menu sent by [SocketioController][cogip.tools.monitor.socketiocontroller.SocketioController].

        Once a menu has been build once, it is cached and reused.

        Arguments:
            new_menu: The new menu information sent by the firmware
        """
        if self.current_menu == new_menu.name:
            return
        self.current_menu = new_menu.name
        widget = self.menu_widgets.get(new_menu.name)
        if not widget:
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            widget.setLayout(layout)

            title = QtWidgets.QLabel(new_menu.name)
            title.setTextFormat(QtCore.Qt.RichText)
            title.setAlignment(QtCore.Qt.AlignHCenter)
            title.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
            title.setStyleSheet("font-weight: bold; color: blue")
            layout.addWidget(title)

            for entry in new_menu.entries:
                if entry.cmd[0] == '_':
                    continue
                cmd_widget = QtWidgets.QWidget()
                cmd_layout = QtWidgets.QHBoxLayout()
                cmd_layout.setContentsMargins(0, 0, 0, 0)
                cmd_widget.setLayout(cmd_layout)
                layout.addWidget(cmd_widget)

                desc, args = split_command(entry.desc)
                button = QtWidgets.QPushButton(desc)
                cmd_layout.addWidget(button)

                for arg in args:
                    edit = QtWidgets.QLineEdit()
                    edit.setPlaceholderText(arg)
                    edit.setToolTip(arg)
                    cmd_layout.addWidget(edit)
                    edit.returnPressed.connect(
                        lambda cmd=entry.cmd, layout=cmd_layout:
                            self.build_command(cmd, layout)
                    )
                button.clicked.connect(
                    lambda cmd=entry.cmd, layout=cmd_layout:
                        self.build_command(cmd, layout)
                )

            layout.addStretch()

            self.menu_widgets[new_menu.name] = widget
            self.menu_staked_widget.addWidget(widget)

        self.menu_staked_widget.setCurrentWidget(widget)

    def build_command(self, cmd: str, layout: QtWidgets.QHBoxLayout):
        """
        Build command to send to [SocketioController][cogip.tools.monitor.socketiocontroller.SocketioController].

        It is built based on the command name given in arguments,
        and arguments strings fetched from the command button in the menu.

        Emit the `signal_send_command` signal with the full command string as argument.

        Arguments:
            cmd: The command name
            layout: The command button containing the command arguments
        """
        i = 1
        while i < layout.count():
            edit = layout.itemAt(i).widget()
            text = edit.text()
            if text == "":
                return
            cmd += f" {text}"
            i += 1
        self.signal_send_command.emit(cmd)

    @qtSlot()
    def add_obstacle(self):
        """
        Qt Slot

        Receive signals from "Add obstacle" action.

        Emit the `signal_add_obstacle` signal.
        """
        self.signal_add_obstacle.emit()

    @qtSlot()
    def load_obstacles(self):
        """
        Qt Slot

        Open a file dialog to select a file and load obstacles from it.
        """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select file to load obstacles",
            dir="",
            filter="JSON Files (*.json)"
        )
        if filename:
            self.signal_load_obstacles.emit(Path(filename))

    @qtSlot()
    def save_obstacles(self):
        """
        Qt Slot

        Open a file dialog to select a file and save obstacles in it.
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Select file to save obstacles",
            dir="",
            filter="JSON Files (*.json)"
        )
        if filename:
            self.signal_save_obstacles.emit(Path(filename))

    @qtSlot()
    def load_cake_layers(self):
        """
        Qt Slot

        Open a file dialog to select a file and load cake layers from it.
        """
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption="Select file to load cake layers",
            dir="",
            filter="JSON Files (*.json)"
        )
        if filename:
            self.signal_load_cake_layers.emit(Path(filename))

    @qtSlot()
    def save_cake_layers(self):
        """
        Qt Slot

        Open a file dialog to select a file and save cake layers in it.
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Select file to save cake layers",
            dir="",
            filter="JSON Files (*.json)",
        )
        if filename:
            self.signal_save_cake_layers.emit(Path(filename))

    def display_help_camera_control(self):
        """
        Qt Slot

        Open camera control help dialog.
        """
        self.help_camera_control.show()
        self.help_camera_control.raise_()
        self.help_camera_control.activateWindow()

    @qtSlot()
    def connected(self, state: bool):
        """
        Qt Slot

        Update the status bar with connected/disconnected state.

        Arguments:
            state: True if connected, False if disconnected
        """
        self.connected_label.setText("Connected" if state else "Disconnected")

    def closeEvent(self, event: QtGui.QCloseEvent):
        settings = QtCore.QSettings("COGIP", "monitor")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("charts_checked", self.view_charts_action.isChecked())
        settings.setValue("dashboard_checked", self.view_dashboard_action.isChecked())
        settings.setValue("camera_params", json.dumps(self.game_view.get_camera_params()))
        super().closeEvent(event)

    def readSettings(self):
        settings = QtCore.QSettings("COGIP", "monitor")
        self.restoreGeometry(settings.value("geometry"))
        self.restoreState(settings.value("windowState"))
        if settings.value("charts_checked") == "true":
            self.charts_toggled(True)
            self.view_charts_action.setChecked(True)
        if settings.value("dashboard_checked") == "true":
            self.dashboard_toggled(True)
            self.view_dashboard_action.setChecked(True)
        try:
            camera_params = json.loads(settings.value("camera_params"))
            self.game_view.set_camera_params(camera_params)
        except Exception:
            pass


def split_command(command: str) -> Tuple[str, List[str]]:
    """
    Split the full command string to separate the name of the command
    and its arguments.

    The command is in the following format:
    ```
    "command name <arg1> <arg2> ..."
    ```

    Arguments:
        command: The command string to split

    Return:
        A tuple of the command name and a list of arguments
    """
    result: List[str] = list()
    arg_match = re.findall(r"(<[\d\w]+>)", command)
    for arg in arg_match:
        result.append(arg[1:-1])
        command = command.replace(arg, "")
    command = command.strip()
    return (command, result)

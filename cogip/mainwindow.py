import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot

from cogip.models import ShellMenu, CtrlModeEnum, RobotState


class MainWindow(QtWidgets.QMainWindow):
    """MainWindow class

    Build the main window of the simulator.

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
    """

    signal_send_command: qtSignal = qtSignal(str)
    signal_add_obstacle: qtSignal = qtSignal()
    signal_load_obstacles: qtSignal = qtSignal(Path)
    signal_save_obstacles: qtSignal = qtSignal(Path)

    def __init__(self, *args, **kwargs):
        """
        """
        super(MainWindow, self).__init__(*args, **kwargs)

        self.menu_widgets: Dict[str, QtWidgets.QWidget] = {}

        self.setWindowTitle('COGIP Simulator')

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        obstacles_menu = menubar.addMenu('&Obstacles')

        # Toolbars
        file_toolbar = self.addToolBar('File')
        obstacles_toolbar = self.addToolBar('Obstacles')

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

        # Actions
        # Icons: https://commons.wikimedia.org/wiki/GNOME_Desktop_icons

        # Exit action
        self.exit_action = QtWidgets.QAction(
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
        self.add_obstacle_action = QtWidgets.QAction(
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
        self.load_obstacles_action = QtWidgets.QAction(
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
        self.save_obstacles_action = QtWidgets.QAction(
            QtGui.QIcon.fromTheme("document-save"),
            'Save obstacles',
            self
        )
        self.save_obstacles_action.setShortcut('Ctrl+S')
        self.save_obstacles_action.setStatusTip('Save obstacles')
        self.save_obstacles_action.triggered.connect(self.save_obstacles)
        obstacles_menu.addAction(self.save_obstacles_action)
        obstacles_toolbar.addAction(self.save_obstacles_action)

        # Console
        dock = QtWidgets.QDockWidget("Console")
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        dock.setWidget(self.log_text)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        file_menu.addAction(dock.toggleViewAction())
        obstacles_menu.addAction(dock.toggleViewAction())

        # Command menu dock
        self.actions_dock = QtWidgets.QDockWidget("Actions")
        self.actions_dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.actions_dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.actions_dock)

        self.current_menu: Optional[str] = None

        # Set a default menu to allocate some space in the UI
        actions_widget = QtWidgets.QWidget()
        actions_layout = QtWidgets.QVBoxLayout()
        actions_widget.setLayout(actions_layout)
        actions_title = QtWidgets.QLabel("No menu loaded")
        actions_title.setTextFormat(QtCore.Qt.RichText)
        actions_title.setAlignment(QtCore.Qt.AlignHCenter)
        actions_title.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        actions_title.setStyleSheet("font-weight: bold; color: blue")
        actions_layout.addWidget(actions_title)
        actions_layout.addStretch()
        self.actions_dock.setWidget(actions_widget)

    @qtSlot(RobotState)
    def new_robot_state(self, state: RobotState):
        """
        Qt Slot

        Update robot position information in the status bar.

        Arguments:
            state: Robot state
        """
        self.pos_mode_text.setText(state.mode.name)
        self.cycle_text.setText(f"{state.cycle or 0:>#6d}")
        self.pos_x_text.setText(f"{state.pose_current.x:> #6.2f}")
        self.pos_y_text.setText(f"{state.pose_current.y:> #6.2f}")
        self.pos_angle_text.setText(f"{state.pose_current.O:> #4.2f}")

    @qtSlot(ShellMenu)
    def load_menu(self, new_menu: ShellMenu):
        """
        Qt Slot

        Display the new menu sent by [SerialController][cogip.serialcontroller.SerialController].

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

        self.actions_dock.setWidget(widget)

    def build_command(self, cmd: str, layout: QtWidgets.QHBoxLayout):
        """
        Build command to send to [SerialController][cogip.serialcontroller.SerialController].

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
            filter="JSON Files (*.json)",
            # Workaround a know Qt bug
            options=QtWidgets.QFileDialog.DontUseNativeDialog
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
            filter="JSON Files (*.json)",
            # Workaround a know Qt bug
            options=QtWidgets.QFileDialog.DontUseNativeDialog
        )
        if filename:
            self.signal_save_obstacles.emit(Path(filename))


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

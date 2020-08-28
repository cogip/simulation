import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot

from cogip.models import ShellMenu, CtrlModeEnum, Pose


class MainWindow(QtWidgets.QMainWindow):
    """MainWindow class

    Build the UI
    """

    trigger_signal = qtSignal(str)

    signal_send_command = qtSignal(str)

    signal_add_obstacle = qtSignal()
    signal_load_obstacles = qtSignal(Path)
    signal_save_obstacles = qtSignal(Path)

    def __init__(self, *args, **kwargs):
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

        pos_x_label = QtWidgets.QLabel("X")
        self.pos_x_text = QtWidgets.QLabel()
        self.pos_x_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.pos_x_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        status_bar.addPermanentWidget(pos_x_label, 0)
        status_bar.addPermanentWidget(self.pos_x_text, 0)

        pos_y_label = QtWidgets.QLabel("Y")
        self.pos_y_text = QtWidgets.QLabel()
        self.pos_y_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.pos_y_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        status_bar.addPermanentWidget(pos_y_label, 0)
        status_bar.addPermanentWidget(self.pos_y_text, 0)

        pos_angle_label = QtWidgets.QLabel("Angle")
        self.pos_angle_text = QtWidgets.QLabel()
        self.pos_angle_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.pos_angle_text.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        status_bar.addPermanentWidget(pos_angle_label, 0)
        status_bar.addPermanentWidget(self.pos_angle_text, 0)

        pos_mode_label = QtWidgets.QLabel("Mode")
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

    @qtSlot(Pose)
    def new_robot_position(self, pose: Pose, mode: CtrlModeEnum):
        self.pos_mode_text.setText(mode.name)
        self.pos_x_text.setText(str(pose.x))
        self.pos_y_text.setText(str(pose.y))
        self.pos_angle_text.setText(str(pose.O))

    @qtSlot(ShellMenu)
    def load_menu(self, new_menu: ShellMenu):
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
        self.signal_add_obstacle.emit()

    @qtSlot()
    def load_obstacles(self):
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
    result: List[str] = list()
    arg_match = re.findall(r"(<[\d\w]+>)", command)
    for arg in arg_match:
        result.append(arg[1:-1])
        command = command.replace(arg, "")
    command = command.strip()
    return (command, result)

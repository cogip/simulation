from PyQt5 import QtCore, QtGui, QtWidgets, QtSerialPort
from PyQt5.QtCore import pyqtSignal as qtSignal
from PyQt5.QtCore import pyqtSlot as qtSlot

import OCC.Display.backend
OCC.Display.backend.load_backend("qt-pyqt5")
import OCC.Display.qtDisplay

from cogip import logger


class MainWindow(QtWidgets.QMainWindow):
    """MainWindow class

    Build the UI
    """

    trigger_signal = qtSignal(str)

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle('COGIP Simulator')

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        view_menu = menubar.addMenu('&View')

        # Status bar
        self.statusBar()

        # Actions
        # self.play_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-start"), 'Play', self)
        # self.pause_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-pause"), 'Pause', self)
        # self.stop_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-stop"), 'Stop', self)
        self.next_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("go-last"), 'Next', self)
        self.next_action.triggered.connect(lambda state: self.trigger_signal.emit('trigger_step'))

        self.exit_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("application-exit"), 'Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(self.close)
        file_menu.addAction(self.exit_action)

        # Toolbar
        toolbar = self.addToolBar('Actions')
        # toolbar.addAction(self.play_action)
        # toolbar.addAction(self.pause_action)
        # toolbar.addAction(self.stop_action)
        toolbar.addAction(self.next_action)
        toolbar.addAction(self.exit_action)

        self.viewer = OCC.Display.qtDisplay.qtViewer3d(self)
        self.viewer.setMinimumSize(640, 480)
        self.viewer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.viewer.InitDriver()
        self.viewer.qApp = QtWidgets.QApplication.instance()
        self.setCentralWidget(self.viewer)

        dock = QtWidgets.QDockWidget("Console")
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)
        self.log_text = QtWidgets.QTextEdit()
        dock.setWidget(self.log_text)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        view_menu.addAction(dock.toggleViewAction())

        dock = QtWidgets.QDockWidget("Status")
        widget = QtWidgets.QWidget()
        dock.setWidget(widget)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        info_grid = QtWidgets.QGridLayout()
        widget.setLayout(info_grid)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        view_menu.addAction(dock.toggleViewAction())

        automaton_state_label = QtWidgets.QLabel("State")
        self.automaton_state_text = QtWidgets.QLineEdit()
        self.automaton_state_text.setReadOnly(True)
        self.automaton_state_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        pos_nb_label = QtWidgets.QLabel("Path Pos")
        self.pos_nb_text = QtWidgets.QLineEdit()
        self.pos_nb_text.setReadOnly(True)
        self.pos_nb_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        pos_x_label = QtWidgets.QLabel("X")
        self.pos_x_text = QtWidgets.QLineEdit()
        self.pos_x_text.setReadOnly(True)
        self.pos_x_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        pos_y_label = QtWidgets.QLabel("Y")
        self.pos_y_text = QtWidgets.QLineEdit()
        self.pos_y_text.setReadOnly(True)
        self.pos_y_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        pos_angle_label = QtWidgets.QLabel("Angle")
        self.pos_angle_text = QtWidgets.QLineEdit()
        self.pos_angle_text.setReadOnly(True)
        self.pos_angle_text.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        info_grid.addWidget(automaton_state_label, 0, 0)
        info_grid.addWidget(self.automaton_state_text, 0, 1)
        info_grid.addWidget(pos_nb_label, 1, 0)
        info_grid.addWidget(self.pos_nb_text, 1, 1)
        info_grid.addWidget(pos_x_label, 2, 0)
        info_grid.addWidget(self.pos_x_text, 2, 1)
        info_grid.addWidget(pos_y_label, 3, 0)
        info_grid.addWidget(self.pos_y_text, 3, 1)
        info_grid.addWidget(pos_angle_label, 4, 0)
        info_grid.addWidget(self.pos_angle_text, 4, 1)        
        info_grid.addItem(QtWidgets.QSpacerItem(0, 0), 5, 0, 1, 2)

        info_grid.setRowStretch(0, 1)
        info_grid.setRowStretch(1, 1)
        info_grid.setRowStretch(2, 1)
        info_grid.setRowStretch(3, 1)
        info_grid.setRowStretch(4, 1)
        info_grid.setRowStretch(5, 10)

        self.actions_dock = QtWidgets.QDockWidget("Actions")
        self.actions_dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.actions_dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.actions_dock)

        self.calibration_menu_main = self.get_calib_menu_main()
        self.calibration_menu_calibration_planner = self.get_calib_menu_calibration_planner()
        self.calibration_menu_calibration_speed_pid = self.get_calib_menu_speed_pid()
        self.calibration_menu_calibration_pos_pid = self.get_calib_menu_pos_pid()

        self.actions_dock.setWidget(self.calibration_menu_main)

    def get_calib_menu_main(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        self.act_menu_calibration_planner = QtWidgets.QPushButton("Planner calibration") # pc
        self.act_menu_calibration_speed_pid = QtWidgets.QPushButton("Speed PID coefficients tuning") # cs
        self.act_menu_calibration_pos_pid = QtWidgets.QPushButton("Pos PID coefficients tuning") # cp
        self.act_main_reboot = QtWidgets.QPushButton("Reboot the node") # reboot
        self.act_main_thread_info = QtWidgets.QPushButton("Prints information about running threads") # ps

        self.act_menu_calibration_planner.clicked.connect(lambda state: self.trigger_signal.emit('trigger_menu_calibration_planner'))
        self.act_menu_calibration_speed_pid.clicked.connect(lambda state: self.trigger_signal.emit('trigger_menu_calibration_speed_pid'))
        self.act_menu_calibration_pos_pid.clicked.connect(lambda state: self.trigger_signal.emit('trigger_menu_calibration_pos_pid'))
        self.act_main_reboot.clicked.connect(lambda state: self.trigger_signal.emit('trigger_main_reboot'))
        self.act_main_thread_info.clicked.connect(lambda state: self.trigger_signal.emit('trigger_main_thread_info'))

        layout.addWidget(self.act_menu_calibration_planner)
        layout.addWidget(self.act_menu_calibration_speed_pid)
        layout.addWidget(self.act_menu_calibration_pos_pid)
        layout.addWidget(self.act_main_reboot)
        layout.addWidget(self.act_main_thread_info)

        layout.addStretch()

        return widget

    def get_calib_menu_calibration_planner(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        self.act_planner_quit = QtWidgets.QPushButton("Quit calibration") # q
        self.act_planner_go_to_next_position = QtWidgets.QPushButton("Go to next position") # n
        self.act_planner_go_to_previous_position = QtWidgets.QPushButton("Go to previous position") # p
        self.act_planner_go_back_to_start_position = QtWidgets.QPushButton("Go back to start position") # s
        self.act_planner_select_next_position = QtWidgets.QPushButton("Select next position") # N
        self.act_planner_select_previous_position = QtWidgets.QPushButton("Select previous position") # P
        self.act_planner_launch_action = QtWidgets.QPushButton("Launch action") # a

        self.act_planner_quit.clicked.connect(lambda state: self.trigger_signal.emit('trigger_planner_quit'))
        self.act_planner_go_to_next_position.clicked.connect(lambda state: self.trigger_signal.emit('trigger_planner_go_to_next_position'))
        self.act_planner_go_to_previous_position.clicked.connect(lambda state: self.trigger_signal.emit('trigger_planner_go_to_previous_position'))
        self.act_planner_go_back_to_start_position.clicked.connect(lambda state: self.trigger_signal.emit('trigger_planner_go_back_to_start_position'))
        self.act_planner_select_next_position.clicked.connect(lambda state: self.trigger_signal.emit('trigger_planner_select_next_position'))
        self.act_planner_select_previous_position.clicked.connect(lambda state: self.trigger_signal.emit('trigger_planner_select_previous_position'))
        self.act_planner_launch_action.clicked.connect(lambda state: self.trigger_signal.emit('trigger_planner_launch_action'))

        layout.addWidget(self.act_planner_quit)
        layout.addWidget(self.act_planner_go_to_next_position)
        layout.addWidget(self.act_planner_go_to_previous_position)
        layout.addWidget(self.act_planner_go_back_to_start_position)
        layout.addWidget(self.act_planner_select_next_position)
        layout.addWidget(self.act_planner_select_previous_position)
        layout.addWidget(self.act_planner_launch_action)

        layout.addStretch()

        return widget

    def get_calib_menu_speed_pid(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        self.act_speed_pid_quit = QtWidgets.QPushButton("Quit calibration") # q
        self.act_speed_pid_send_reset = QtWidgets.QPushButton("Send reset") # r
        self.act_speed_pid_linear_speed_charac = QtWidgets.QPushButton("Linear speed characterization") # l
        self.act_speed_pid_angular_speed_charac = QtWidgets.QPushButton("Angular speed characterization") # a
        self.act_speed_pid_linear_speed_test = QtWidgets.QPushButton("Linear speed PID test") # L
        self.act_speed_pid_angular_speed_test = QtWidgets.QPushButton("Angular speed PID test") # A

        self.act_speed_pid_quit.clicked.connect(lambda state: self.trigger_signal.emit('trigger_speed_pid_quit'))
        self.act_speed_pid_send_reset.clicked.connect(lambda state: self.trigger_signal.emit('trigger_speed_pid_send_reset'))
        self.act_speed_pid_linear_speed_charac.clicked.connect(lambda state: self.trigger_signal.emit('trigger_speed_pid_linear_speed_charac'))
        self.act_speed_pid_angular_speed_charac.clicked.connect(lambda state: self.trigger_signal.emit('trigger_speed_pid_angular_speed_charac'))
        self.act_speed_pid_linear_speed_test.clicked.connect(lambda state: self.trigger_signal.emit('trigger_speed_pid_linear_speed_test'))
        self.act_speed_pid_angular_speed_test.clicked.connect(lambda state: self.trigger_signal.emit('trigger_speed_pid_angular_speed_test'))

        layout.addWidget(self.act_speed_pid_quit)
        layout.addWidget(self.act_speed_pid_send_reset)
        layout.addWidget(self.act_speed_pid_linear_speed_charac)
        layout.addWidget(self.act_speed_pid_angular_speed_charac)
        layout.addWidget(self.act_speed_pid_linear_speed_test)
        layout.addWidget(self.act_speed_pid_angular_speed_test)

        layout.addStretch()

        return widget

    def get_calib_menu_pos_pid(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        self.act_pos_pid_quit = QtWidgets.QPushButton("Quit calibration") # q
        self.act_pos_pid_send_reset = QtWidgets.QPushButton("Send reset") # r
        self.act_pos_pid_speed_linear_kp = QtWidgets.QPushButton("Speed linear Kp calibration") # a
        self.act_pos_pid_speed_angular_kp = QtWidgets.QPushButton("Speed angular Kp calibration") # A

        self.act_pos_pid_quit.clicked.connect(lambda state: self.trigger_signal.emit('trigger_pos_pid_quit'))
        self.act_pos_pid_send_reset.clicked.connect(lambda state: self.trigger_signal.emit('trigger_pos_pid_send_reset'))
        self.act_pos_pid_speed_linear_kp.clicked.connect(lambda state: self.trigger_signal.emit('trigger_pos_pid_speed_linear_kp'))
        self.act_pos_pid_speed_angular_kp.clicked.connect(lambda state: self.trigger_signal.emit('trigger_pos_pid_speed_angular_kp'))

        layout.addWidget(self.act_pos_pid_quit)
        layout.addWidget(self.act_pos_pid_send_reset)
        layout.addWidget(self.act_pos_pid_speed_linear_kp)
        layout.addWidget(self.act_pos_pid_speed_angular_kp)

        layout.addStretch()

        return widget

    def onPlayClick(self, s):
        pass

    def onPauseClick(self, s):
        pass

    def onStopClick(self, s):
        pass

    @qtSlot(str)
    def new_controller_state(self, new_state: str):
        logger.debug(f"new_controller_state({new_state})")
        self.automaton_state_text.setText(new_state)
        if new_state == 'menu_main':
            self.actions_dock.setWidget(self.calibration_menu_main)
        elif new_state == 'menu_calibration_planner':
            self.actions_dock.setWidget(self.calibration_menu_calibration_planner)
        elif new_state == 'menu_calibration_speed_pid':
            self.actions_dock.setWidget(self.calibration_menu_calibration_speed_pid)
        elif new_state == 'menu_calibration_pos_pid':
            self.actions_dock.setWidget(self.calibration_menu_calibration_pos_pid)

        elif new_state == 'starting':
            self.next_action.setEnabled(False)
        elif new_state == 'waiting_calibration_mode':
            self.next_action.setEnabled(False)
        elif new_state == 'paused':
            self.next_action.setEnabled(True)
        elif new_state == 'stepping':
            self.next_action.setEnabled(False)

    @qtSlot(float, float, float)
    def new_robot_position(self, x: float, y: float, angle: float):
        self.pos_x_text.setText(str(x))
        self.pos_y_text.setText(str(y))
        self.pos_angle_text.setText(str(angle))

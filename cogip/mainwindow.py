from PyQt5 import QtCore, QtGui, QtWidgets, QtSerialPort
from PyQt5.QtCore import pyqtSignal as qtSignal
from PyQt5.QtCore import pyqtSlot as qtSlot

import OCC.Display.backend
OCC.Display.backend.load_backend("qt-pyqt5")
import OCC.Display.qtDisplay

class MainWindow(QtWidgets.QMainWindow):
    """MainWindow class

    Build the UI
    """

    trigger_signal = qtSignal(str)
    
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle('COGIP Simulator')

        ## Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        view_menu = menubar.addMenu('&View')

        ## Status bar
        self.statusBar()

        ## Actions
        self.play_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-start"), 'Play', self)
        # self.play_action.setCheckable(True)
        self.play_action.triggered.connect(self.onPlayClick)

        self.pause_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-pause"), 'Pause', self)
        # self.pause_action.setCheckable(True)
        self.pause_action.triggered.connect(self.onPauseClick)
        
        self.stop_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("media-playback-stop"), 'Stop', self)
        # self.stop_action.setCheckable(True)
        self.stop_action.triggered.connect(self.onStopClick)

        self.next_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("go-last"), 'Next', self)
        self.next_action.triggered.connect(self.onNextClick)

        self.exit_action = QtWidgets.QAction(QtGui.QIcon.fromTheme("application-exit"), 'Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(self.onExitClick)
        file_menu.addAction(self.exit_action)

        ## Toolbar
        toolbar = self.addToolBar('Actions')
        toolbar.addAction(self.play_action)
        toolbar.addAction(self.pause_action)
        toolbar.addAction(self.stop_action)
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
        self.automaton_state_text.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        
        pos_nb_label = QtWidgets.QLabel("Path Pos")
        self.pos_nb_text = QtWidgets.QLineEdit()
        self.pos_nb_text.setReadOnly(True)
        self.pos_nb_text.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        
        pos_x_label = QtWidgets.QLabel("X")
        self.pos_x_text = QtWidgets.QLineEdit()
        self.pos_x_text.setReadOnly(True)
        self.pos_x_text.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

        pos_y_label = QtWidgets.QLabel("Y")
        self.pos_y_text = QtWidgets.QLineEdit()
        self.pos_y_text.setReadOnly(True)
        self.pos_y_text.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        
        pos_angle_label = QtWidgets.QLabel("Angle")
        self.pos_angle_text = QtWidgets.QLineEdit()
        self.pos_angle_text.setReadOnly(True)
        self.pos_angle_text.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

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
        info_grid.addItem(QtWidgets.QSpacerItem(0,0), 5, 0, 1, 2)

        info_grid.setRowStretch(0, 1)
        info_grid.setRowStretch(1, 1)
        info_grid.setRowStretch(2, 1)
        info_grid.setRowStretch(3, 1)
        info_grid.setRowStretch(4, 1)
        info_grid.setRowStretch(5, 10)

    def onPlayClick(self, s):
        pass

    def onPauseClick(self, s):
        pass

    def onStopClick(self, s):
        pass

    def onNextClick(self, s):
        self.trigger_signal.emit('trigger_step')
        
    def onExitClick(self, s):
        self.close()

    @qtSlot(str)
    def new_controller_state(self, new_state: str):
        self.automaton_state_text.setText(new_state)
        if new_state == 'state_stopped':
            self.play_action.setEnabled(True)
            self.next_action.setEnabled(False)
            self.pause_action.setEnabled(False)
            self.stop_action.setEnabled(False)
        elif new_state == 'state_starting':
            self.play_action.setEnabled(False)
            self.next_action.setEnabled(False)
            self.pause_action.setEnabled(False)
            self.stop_action.setEnabled(False)
        elif new_state == 'state_waiting_calibration_mode':
            self.play_action.setEnabled(False)
            self.next_action.setEnabled(False)
            self.pause_action.setEnabled(False)
            self.stop_action.setEnabled(False)
        elif new_state == 'state_paused':
            self.play_action.setEnabled(False)
            self.next_action.setEnabled(True)
            self.pause_action.setEnabled(False)
            self.stop_action.setEnabled(True)
        elif new_state == 'state_stepping':
            self.play_action.setEnabled(False)
            self.next_action.setEnabled(False)
            self.pause_action.setEnabled(False)
            self.stop_action.setEnabled(False)

    @qtSlot(float, float, float)
    def new_robot_position(self, x: float, y: float, angle: float):
        self.pos_x_text.setText(str(x))
        self.pos_y_text.setText(str(y))
        self.pos_angle_text.setText(str(angle))

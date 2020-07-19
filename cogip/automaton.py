from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal as qtSignal
from PyQt5.QtCore import pyqtSlot as qtSlot

from cogip import logger


class Automaton(QtCore.QObject):
    """Automaton class

    Use a :class:`~QtCore.QStateMachine` to handle the current state of the simulation and its transitions.
    """

    #: :obj:`qtSignal(str)`:
    #:      Qt signal emitted to update the automaton state.
    #:
    #:      Connected to :class:`~cogip.mainwindow.MainWindow`.
    signal_new_state = qtSignal(str)

    signal_enter_new_state = qtSignal(str)

    # Create state machine signals
    trigger_menu_calibration_speed_pid = qtSignal()
    trigger_menu_calibration_pos_pid = qtSignal()
    trigger_menu_calibration_planner = qtSignal()
    trigger_main_reboot = qtSignal()
    trigger_main_thread_info = qtSignal()

    trigger_planner_quit = qtSignal()
    trigger_planner_go_to_next_position = qtSignal()
    trigger_planner_go_to_previous_position = qtSignal()
    trigger_planner_go_back_to_start_position = qtSignal()
    trigger_planner_select_next_position = qtSignal()
    trigger_planner_select_previous_position = qtSignal()
    trigger_planner_launch_action = qtSignal()

    trigger_speed_pid_quit = qtSignal()
    trigger_speed_pid_send_reset = qtSignal()
    trigger_speed_pid_linear_speed_charac = qtSignal()
    trigger_speed_pid_angular_speed_charac = qtSignal()
    trigger_speed_pid_linear_speed_test = qtSignal()
    trigger_speed_pid_angular_speed_test = qtSignal()

    trigger_pos_pid_quit = qtSignal()
    trigger_pos_pid_send_reset = qtSignal()
    trigger_pos_pid_speed_linear_kp = qtSignal()
    trigger_pos_pid_speed_angular_kp = qtSignal()

    trigger_waiting_calibration_mode = qtSignal()
    trigger_menu_main = qtSignal()
    trigger_position_reached = qtSignal()

    def __init__(self):
        QtCore.QObject.__init__(self)

        self.previous_state = None

        # Create state machine
        self.state_machine = QtCore.QStateMachine()

        # Create states
        self.state_starting = QtCore.QState()
        self.state_starting.setObjectName('state_starting')
        self.state_waiting_calibration_mode = QtCore.QState()
        self.state_waiting_calibration_mode.setObjectName('state_waiting_calibration_mode')

        self.state_menu_main = QtCore.QState()
        self.state_menu_main.setObjectName('state_menu_main')
        self.state_menu_calibration_planner = QtCore.QState()
        self.state_menu_calibration_planner.setObjectName('state_menu_calibration_planner')
        self.state_menu_calibration_speed_pid = QtCore.QState()
        self.state_menu_calibration_speed_pid.setObjectName('state_menu_calibration_speed_pid')
        self.state_menu_calibration_pos_pid = QtCore.QState()
        self.state_menu_calibration_pos_pid.setObjectName('state_menu_calibration_pos_pid')

        self.state_planner_go_to_next_position = QtCore.QState()
        self.state_planner_go_to_next_position.setObjectName('state_planner_go_to_next_position')

        self.state_speed_pid_linear_speed_charac = QtCore.QState()
        self.state_speed_pid_linear_speed_charac.setObjectName('state_speed_pid_linear_speed_charac')
        self.state_speed_pid_angular_speed_charac = QtCore.QState()
        self.state_speed_pid_angular_speed_charac.setObjectName('state_speed_pid_angular_speed_charac')

        self.state_pos_pid_speed_linear_kp = QtCore.QState()
        self.state_pos_pid_speed_linear_kp.setObjectName('state_pos_pid_speed_linear_kp')

        # Create transitions
        self.state_starting.addTransition(self.trigger_waiting_calibration_mode, self.state_waiting_calibration_mode)
        self.state_waiting_calibration_mode.addTransition(self.trigger_menu_main, self.state_menu_main)

        self.state_menu_main.addTransition(self.trigger_menu_calibration_planner, self.state_menu_calibration_planner)
        self.state_menu_main.addTransition(self.trigger_menu_calibration_speed_pid, self.state_menu_calibration_speed_pid)
        self.state_menu_main.addTransition(self.trigger_menu_calibration_pos_pid, self.state_menu_calibration_pos_pid)

        self.state_menu_calibration_planner.addTransition(self.trigger_planner_quit, self.state_menu_main)
        self.state_menu_calibration_planner.addTransition(self.trigger_planner_go_to_next_position, self.state_planner_go_to_next_position)
        self.state_planner_go_to_next_position.addTransition(self.trigger_position_reached, self.state_menu_calibration_planner)

        self.state_menu_calibration_speed_pid.addTransition(self.trigger_speed_pid_quit, self.state_menu_main)
        self.state_menu_calibration_speed_pid.addTransition(self.trigger_speed_pid_linear_speed_charac, self.state_speed_pid_linear_speed_charac)
        self.state_speed_pid_linear_speed_charac.addTransition(self.trigger_position_reached, self.state_menu_calibration_speed_pid)
        self.state_menu_calibration_speed_pid.addTransition(self.trigger_speed_pid_angular_speed_charac, self.state_speed_pid_angular_speed_charac)
        self.state_speed_pid_angular_speed_charac.addTransition(self.trigger_position_reached, self.state_menu_calibration_speed_pid)

        self.state_menu_calibration_pos_pid.addTransition(self.trigger_pos_pid_quit, self.state_menu_main)
        self.state_menu_calibration_pos_pid.addTransition(self.trigger_pos_pid_speed_linear_kp, self.state_pos_pid_speed_linear_kp)
        self.state_pos_pid_speed_linear_kp.addTransition(self.trigger_position_reached, self.state_menu_calibration_pos_pid)

        # Create actions
        self.state_starting.onEntry = self.enter_state
        self.state_starting.onExit = self.exit_state
        self.state_waiting_calibration_mode.onEntry = self.enter_state
        self.state_waiting_calibration_mode.onExit = self.exit_state

        self.state_menu_main.onEntry = self.enter_state
        self.state_menu_main.onExit = self.exit_state
        self.state_menu_calibration_planner.onEntry = self.enter_state
        self.state_menu_calibration_planner.onExit = self.exit_state
        self.state_menu_calibration_speed_pid.onEntry = self.enter_state
        self.state_menu_calibration_speed_pid.onExit = self.exit_state
        self.state_menu_calibration_pos_pid.onEntry = self.enter_state
        self.state_menu_calibration_pos_pid.onExit = self.exit_state

        self.state_planner_go_to_next_position.onEntry = self.enter_state
        self.state_planner_go_to_next_position.onExit = self.exit_state

        self.state_speed_pid_linear_speed_charac.onEntry = self.enter_state
        self.state_speed_pid_linear_speed_charac.onExit = self.exit_state
        self.state_speed_pid_angular_speed_charac.onEntry = self.enter_state
        self.state_speed_pid_angular_speed_charac.onExit = self.exit_state

        self.state_pos_pid_speed_linear_kp.onEntry = self.enter_state
        self.state_pos_pid_speed_linear_kp.onExit = self.exit_state

        # Add states
        self.state_machine.addState(self.state_starting)
        self.state_machine.addState(self.state_waiting_calibration_mode)
        self.state_machine.addState(self.state_menu_main)
        self.state_machine.addState(self.state_menu_calibration_planner)
        self.state_machine.addState(self.state_menu_calibration_speed_pid)
        self.state_machine.addState(self.state_menu_calibration_pos_pid)

        self.state_machine.setInitialState(self.state_starting)

        self.state_machine.start()

    @qtSlot(str)
    def new_trigger(self, trigger: str):
        if hasattr(self, trigger):
            state = self.state_machine.configuration().copy().pop()
            logger.info(f"Emit automaton signal: {trigger} ({state.objectName()})")
            getattr(self, trigger).emit()

    @qtSlot(QtCore.QStateMachine.SignalEvent)
    def enter_state(self, event: QtCore.QStateMachine.SignalEvent):
        new_state = self.state_machine.configuration().copy().pop()
        new_state_name = new_state.objectName().partition("state_")[-1]
        logger.info(f"Entered '{new_state.objectName()}'")

        self.signal_new_state.emit(new_state_name)

        if new_state_name == "enter_menu_main" and self.previous_state in [
            "state_menu_calibration_planner",
            "state_menu_calibration_speed_pid",
            "state_menu_calibration_pos_pid"
        ]:
            self.signal_enter_new_state.emit("quit_menu")
        else:
            self.signal_enter_new_state.emit(new_state_name)

    @qtSlot(QtCore.QStateMachine.SignalEvent)
    def exit_state(self, event: QtCore.QStateMachine.SignalEvent):
        state = self.state_machine.configuration().copy().pop()
        self.previous_state = state.objectName()
        logger.info(f"Exited '{self.previous_state}'")

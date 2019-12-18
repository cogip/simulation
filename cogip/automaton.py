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
    signal_new_automaton_state = qtSignal(str)


    #: :obj:`qtSignal()`:
    #:      Qt signal emitted when the automaton enters the `enter_shell` state.
    #:
    #:      Connected to :class:`~cogip.serialcontroller.SerialController`.
    signal_enter_shell = qtSignal()

    #: :obj:`qtSignal()`:
    #:      Qt signal emitted when the automaton enters the `next_position` state.
    #:
    #:      Connected to :class:`~cogip.serialcontroller.SerialController`.
    signal_next_position = qtSignal()
    
    # Create state machine signals
    trigger_wait_calib = qtSignal()
    trigger_shell_started = qtSignal()
    trigger_step = qtSignal()
    trigger_move = qtSignal()
    trigger_position_reached = qtSignal()

    def __init__(self):
        QtCore.QObject.__init__(self)

        # Create state machine
        self.state_machine = QtCore.QStateMachine()

        # Create states
        self.state_starting = QtCore.QState()
        self.state_starting.setObjectName('state_starting')
        self.state_waiting_calibration_mode = QtCore.QState()
        self.state_waiting_calibration_mode.setObjectName('state_waiting_calibration_mode')
        self.state_paused = QtCore.QState()
        self.state_paused.setObjectName('state_paused')
        self.state_stepping = QtCore.QState()
        self.state_stepping.setObjectName('state_stepping')
        self.state_moving = QtCore.QState()
        self.state_moving.setObjectName('state_moving')
        
        # Create transitions
        self.state_starting.addTransition(self.trigger_wait_calib, self.state_waiting_calibration_mode)
        self.state_waiting_calibration_mode.addTransition(self.trigger_shell_started, self.state_paused)
        self.state_paused.addTransition(self.trigger_step, self.state_stepping)
        self.state_stepping.addTransition(self.trigger_move, self.state_moving)
        self.state_moving.addTransition(self.trigger_position_reached, self.state_paused)

        # Create actions
        self.state_starting.onEntry = self.print_on_enter
        self.state_starting.onExit = self.print_on_exit
        self.state_waiting_calibration_mode.onEntry = self.automaton_enter_shell
        self.state_waiting_calibration_mode.onExit = self.print_on_exit
        self.state_paused.onEntry = self.print_on_enter
        self.state_paused.onExit = self.print_on_exit
        self.state_stepping.onEntry = self.automaton_next
        self.state_stepping.onExit = self.print_on_exit
        self.state_moving.onEntry = self.print_on_enter
        self.state_moving.onExit = self.print_on_exit

        # Add states
        self.state_machine.addState(self.state_starting)
        self.state_machine.addState(self.state_waiting_calibration_mode)
        self.state_machine.addState(self.state_paused)
        self.state_machine.addState(self.state_stepping)
        self.state_machine.addState(self.state_moving)

        self.state_machine.setInitialState(self.state_starting)
        
        self.state_machine.start()

    @qtSlot(str)
    def new_trigger(self, state: str):
        if hasattr(self, state):
            getattr(self, state).emit()
            
    @qtSlot(QtCore.QStateMachine.SignalEvent)
    def print_on_enter(self, event: QtCore.QStateMachine.SignalEvent):
        state = self.state_machine.configuration().copy().pop()
        logger.info(f"Entered '{state.objectName()}'")
        self.signal_new_automaton_state.emit(state.objectName())
        
    @qtSlot(QtCore.QStateMachine.SignalEvent)
    def print_on_exit(self, event: QtCore.QStateMachine.SignalEvent):
        state = self.state_machine.configuration().copy().pop()
        logger.info(f"Exited '{state.objectName()}'")

    @qtSlot(QtCore.QStateMachine.SignalEvent)
    def automaton_enter_shell(self, event: QtCore.QStateMachine.SignalEvent):
        self.print_on_enter(event)
        self.signal_enter_shell.emit()

    @qtSlot(QtCore.QStateMachine.SignalEvent)
    def automaton_next(self, event: QtCore.QStateMachine.SignalEvent):
        self.print_on_enter(event)
        self.signal_next_position.emit()

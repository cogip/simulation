from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal as qtSignal

from cogip.models.actuators import (
    ActuatorsState, ActuatorCommand,
    ServoEnum, Servo, ServoCommand,
    PumpEnum, Pump, PumpCommand
)


class ServoControl(QtCore.QObject):
    """
    ServoControl class.

    Build a widget to control a servo.
    """
    command_updated: qtSignal = qtSignal(ServoCommand)

    def __init__(self, servo: Servo, layout: QtWidgets.QGridLayout):
        """
        Class constructor.

        Arguments:
            servo: servo to control
            layout: The parent layout
        """
        super().__init__()
        position_schema = servo.model_json_schema()["properties"]["position"]
        self._id = servo.id

        row = layout.rowCount()
        minimum = position_schema.get("minimum")
        maximum = position_schema.get("maximum")

        label = QtWidgets.QLabel(self._id.name)
        layout.addWidget(label, row, 0)

        kind = QtWidgets.QLabel("Servo")
        layout.addWidget(kind, row, 1)

        self._command = QtWidgets.QSpinBox()
        self._command.setToolTip("Position command")
        self._command.setMinimum(minimum)
        self._command.setMaximum(maximum)
        self._command.setSingleStep(1)
        self._command.setValue(servo.position)
        self._command.valueChanged.connect(self.command_changed)
        layout.addWidget(self._command, row, 2)

        self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._slider.setToolTip("Position command")
        self._slider.setMinimum(minimum)
        self._slider.setMaximum(maximum)
        self._slider.setSingleStep(1)
        self._slider.setValue(servo.position)
        self._slider.valueChanged.connect(self._command.setValue)
        layout.addWidget(self._slider, row, 3)

        self._position = QtWidgets.QLabel(str(servo.position))
        self._position.setToolTip("Current position")
        layout.addWidget(self._position, row, 4)

    def command_changed(self, value):
        self._slider.setValue(value)
        command = ServoCommand(id=self._id, command=value)
        self.command_updated.emit(command)

    def update_value(self, servo: Servo):
        self._position.setText(str(servo.position))


class PumpControl(QtCore.QObject):
    """
    PumpControl class.

    Build a widget to control a pump.
    """
    command_updated: qtSignal = qtSignal(PumpCommand)

    def __init__(self, pump: Pump, layout: QtWidgets.QGridLayout):
        """
        Class constructor.

        Arguments:
            pump: pump to control
            layout: The parent layout
        """
        super().__init__()
        self._id = pump.id

        row = layout.rowCount()

        label = QtWidgets.QLabel(self._id.name)
        layout.addWidget(label, row, 0)

        kind = QtWidgets.QLabel("Pump")
        layout.addWidget(kind, row, 1)

        self._command = QtWidgets.QCheckBox()
        self._command.setChecked(pump.activated)
        self._command.toggled.connect(self.command_changed)
        layout.addWidget(self._command, row, 2)

        self._under_pressure = QtWidgets.QCheckBox()
        self._under_pressure.setToolTip("Under pressure")
        self._under_pressure.setChecked(pump.under_pressure)
        self._under_pressure.setEnabled(False)
        layout.addWidget(self._under_pressure, row, 4)

    def command_changed(self, checked: bool):
        command = PumpCommand(id=self._id, command=checked)
        self.command_updated.emit(command)

    def update_value(self, pump: Pump):
        self._under_pressure.setChecked(pump.under_pressure)


class ActuatorsDialog(QtWidgets.QDialog):
    """
    ActuatorsDialog class

    Build a modal for actuators remote control.

    Attributes:
        new_actuator_command: Qt signal emitted when a actuator command is updated
        closed: Qt signal emitted when the window is hidden
    """
    new_actuator_command: qtSignal = qtSignal(int, object)
    closed: qtSignal = qtSignal(int)

    def __init__(self, actuators_state: ActuatorsState, parent: QtWidgets.QWidget = None):
        """
        Class constructor.

        Arguments:
            actuators_state: initial state of actuators
            parent: The parent widget
        """
        super().__init__(parent)
        self._robot_id: int = actuators_state.robot_id
        self._servos: dict[ServoEnum, ServoControl] = {}
        self._pumps: dict[PumpEnum, PumpControl] = {}
        self.setWindowTitle(f"Actuators Control {self._robot_id}")
        self.setModal(False)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        for servo in actuators_state.servos:
            self._servos[servo.id] = ServoControl(servo, layout)
            self._servos[servo.id].command_updated.connect(self.command_updated)
        for pump in actuators_state.pumps:
            self._pumps[pump.id] = PumpControl(pump, layout)
            self._pumps[pump.id].command_updated.connect(self.command_updated)

        self.readSettings()

    def update_actuators(self, actuators_state: ActuatorsState):
        """
        Update actuators with new values.

        Arguments:
            actuators_state: current state of actuators
        """
        for servo in actuators_state.servos:
            if servo.id in self._servos:
                self._servos[servo.id].update_value(servo)
        for pump in actuators_state.pumps:
            if pump.id in self._pumps:
                self._pumps[pump.id].update_value(pump)

    def command_updated(self, command: ActuatorCommand):
        """
        Emit updated values with namespace, name and value.
        """
        self.new_actuator_command.emit(self._robot_id, command)

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Hide the window.

        Arguments:
            event: The close event (unused)
        """
        settings = QtCore.QSettings("COGIP", "monitor")
        settings.setValue(f"properties/actuators/{self._robot_id}", self.saveGeometry())

        self.closed.emit(self._robot_id)
        event.accept()
        super().closeEvent(event)

    def readSettings(self):
        settings = QtCore.QSettings("COGIP", "monitor")
        self.restoreGeometry(settings.value(f"properties/actuators/{self._robot_id}"))

import collections
from typing import Any, Dict, OrderedDict

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal as qtSignal

from .. import logger


class IntegerProperty(QtCore.QObject):
    """
    IntegerProperty class.

    Build a widget to configure a integer property.
    """
    value_updated: qtSignal = qtSignal(str, int)

    def __init__(self, name: str, props: Dict[str, Any], layout: QtWidgets.QGridLayout):
        """
        Class constructor.

        Arguments:
            name: property name
            props: properties of the integer property
            layout: The parent layout
        """
        super().__init__()
        self._name = name

        row = layout.rowCount()
        minimum = props.get("minimum")
        maximum = props.get("maximum")
        step = props.get("multipleOf", 1)
        help = props.get("description")
        self._slider = None

        label = QtWidgets.QLabel(props["title"])
        label.setToolTip(help)
        layout.addWidget(label, row, 0)

        self._value = QtWidgets.QSpinBox()
        self._value.setToolTip(help)
        self._value.valueChanged.connect(self.value_changed)
        if minimum is not None:
            self._value.setMinimum(minimum)
        if maximum is not None:
            self._value.setMaximum(maximum)
        self._value.setSingleStep(step)
        self._value.setValue(props["value"])
        layout.addWidget(self._value, row, 1)

        if minimum is not None and maximum is not None:
            self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self._slider.setToolTip(help)
            self._slider.setMinimum(minimum)
            self._slider.setMaximum(maximum)
            self._slider.setSingleStep(step)
            self._slider.setValue(props["value"])
            self._slider.valueChanged.connect(self._value.setValue)
            layout.addWidget(self._slider, row, 2)

    def value_changed(self, value):
        if self._slider:
            self._slider.setValue(value)
        self.value_updated.emit(self._name, value)

    def update_value(self, value):
        self._value.blockSignals(True)
        self._value.setValue(value)
        self._value.blockSignals(False)
        if self._slider:
            self._slider.blockSignals(True)
            self._slider.setValue(value)
            self._slider.blockSignals(False)


class NumberProperty(QtCore.QObject):
    """
    NumberProperty class.

    Build a widget to configure a number property.
    """
    value_updated: qtSignal = qtSignal(str, float)

    def __init__(self, name: str, props: Dict[str, Any], layout: QtWidgets.QGridLayout):
        """
        Class constructor.

        Arguments:
            name: property name
            props: properties of the number property
            layout: The parent layout
        """
        super().__init__()
        self._name = name

        row = layout.rowCount()
        minimum = props.get("minimum")
        maximum = props.get("maximum")
        step = props.get("multipleOf", 0.1)
        self._slider = None

        label = QtWidgets.QLabel(props["title"])
        layout.addWidget(label, row, 0)

        self._value = QtWidgets.QDoubleSpinBox()
        self._value.valueChanged.connect(self.value_changed)
        if minimum is not None:
            self._value.setMinimum(minimum)
        if maximum is not None:
            self._value.setMaximum(maximum)
        self._value.setSingleStep(step)
        self._value.setValue(props["value"])
        layout.addWidget(self._value, row, 1)

        if minimum is not None and maximum is not None:
            self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self._slider.setMinimum(minimum * 100)
            self._slider.setMaximum(maximum * 100)
            self._slider.setSingleStep(step * 100)
            self._slider.setValue(props["value"] * 100)
            self._slider.valueChanged.connect(
                lambda v: self._value.setValue(v / 100)
            )
            layout.addWidget(self._slider, row, 2)

    def value_changed(self, value):
        if self._slider:
            self._slider.setValue(value * 100)
        self.value_updated.emit(self._name, value)

    def update_value(self, value):
        self._value.blockSignals(True)
        self._value.setValue(value)
        self._value.blockSignals(False)
        if self._slider:
            self._slider.blockSignals(True)
            self._slider.setValue(value * 100)
            self._slider.blockSignals(False)


class PropertiesDialog(QtWidgets.QDialog):
    """
    PropertiesDialog class

    Build a modal for properties configuration.

    Attributes:
        property_updated: Qt signal emitted when a property is updated
        closed: Qt signal emitted when the window is hidden
    """
    property_updated: qtSignal = qtSignal(dict)
    closed: qtSignal = qtSignal()

    def __init__(self, config: Dict[str, Any], parent: QtWidgets.QWidget = None):
        """
        Class constructor.

        Arguments:
            config: JSON Schema of properties with current values and namespace
            parent: The parent widget
        """
        super().__init__(parent)
        self._config = config
        self._properties: OrderedDict[str, IntegerProperty] = collections.OrderedDict()
        self.setWindowTitle(config["title"])
        self.setModal(False)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        for name, props in config["properties"].items():
            match type := props["type"]:
                case "integer":
                    self._properties[name] = IntegerProperty(name, props, layout)
                    self._properties[name].value_updated.connect(self.value_updated)
                case "number":
                    self._properties[name] = NumberProperty(name, props, layout)
                    self._properties[name].value_updated.connect(self.value_updated)
                case _:
                    logger.error(f"Unsupported property type: {type}")

        self.readSettings()

    def update_values(self, config: Dict[str, Any]):
        """
        Update properties with new values.

        Arguments:
            config: JSON Schema of properties with current values and namespace
        """
        for name, props in config["properties"].items():
            if property := self._properties.get(name):
                property.update_value(props["value"])

    def value_updated(self, name: str, value: int | float):
        """
        Emit updated values with namespace, name and value.
        """
        self.property_updated.emit({
            "namespace": self._config["namespace"],
            "name": name,
            "value": value
        })

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Hide the window.

        Arguments:
            event: The close event (unused)
        """
        settings = QtCore.QSettings("COGIP", "monitor")
        settings.setValue(f"properties/{self._config['namespace']}", self.saveGeometry())

        self.closed.emit()
        event.accept()
        super().closeEvent(event)

    def readSettings(self):
        settings = QtCore.QSettings("COGIP", "monitor")
        self.restoreGeometry(settings.value(f"properties/{self._config['namespace']}"))

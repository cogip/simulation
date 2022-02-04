import csv
from pathlib import Path
from typing import Optional

from PySide6 import QtCharts, QtCore, QtGui, QtWidgets
from PySide6.QtCore import Slot as qtSlot
from PySide6.QtCore import Signal as qtSignal

from cogip.models import RobotState, CtrlModeEnum


class ChartView(QtWidgets.QWidget):
    """ChartsView class

    Chart widget displaying a graph with a 'current' and an 'order' curve.

    It features a scrollbar, a zoom slider and a button to save the data in CVS format.

    The chart is reset after the robot mode has changed from RUNNING to an other value.

    Attributes:
        need_reset: True if the data must be reset on next state
        slider_events_disabled: Do not recalculate range if False
        default_range_max_x: Default max X range value
        default_range_max_y: Default max Y range value
        range_max_x: Current max X range value
        range_max_y: Current max Y range value
        zoom_max: max zoom value
    """

    need_reset: bool = False
    slider_events_disabled: bool = False
    default_range_max_x: int = 100
    default_range_max_y: int = 20
    range_max_x: int = default_range_max_x
    range_max_y: int = default_range_max_y
    zoom_max: int = 10

    def __init__(self, parent=None, name: Optional[str] = None):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
            name: Name of the current chart
        """
        super().__init__(parent)
        self.name = name

        layout = QtWidgets.QVBoxLayout(self)

        self.chart_view = QtCharts.QChartView()
        self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        layout.addWidget(self.chart_view)

        sliders_widget = QtWidgets.QWidget()
        sliders_layout = QtWidgets.QGridLayout(sliders_widget)
        sliders_widget.setLayout(sliders_layout)
        layout.addWidget(sliders_widget)

        self.scrollbar = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        self.scrollbar.setMinimum(1)
        self.scrollbar.setMaximum(self.default_range_max_x)
        self.scrollbar.setSliderPosition(25)
        self.scrollbar.valueChanged.connect(self.slider_changed)
        sliders_layout.addWidget(self.scrollbar, 0, 0)

        self.zoom = QtWidgets.QSlider(QtCore.Qt.Horizontal, minimum=0, maximum=100, value=60)
        self.zoom.setMinimum(1)
        self.zoom.setMaximum(self.zoom_max)
        self.zoom.setValue(1)
        self.zoom.valueChanged.connect(self.slider_changed)
        sliders_layout.addWidget(self.zoom, 1, 0)

        self.save_button = QtWidgets.QPushButton()
        self.save_button.setIcon(QtGui.QIcon.fromTheme("document-save"))
        self.save_button.setStatusTip('Save values')
        self.save_button.clicked.connect(self.save_values)
        sliders_layout.addWidget(self.save_button, 0, 1, 2, 1)

        self.chart = QtCharts.QChart()

        self.serie_current = QtCharts.QLineSeries(name=f"{self.name} Current")
        self.chart.addSeries(self.serie_current)
        pen = self.serie_current.pen()
        pen.setWidth(5)
        self.serie_current.setPen(pen)

        self.serie_order = QtCharts.QLineSeries(name=f"{self.name} Order")
        self.chart.addSeries(self.serie_order)
        pen = self.serie_order.pen()
        pen.setWidth(5)
        self.serie_order.setPen(pen)

        self.chart.createDefaultAxes()

        self.chart.axisX(self.serie_current).setMin(1)
        self.chart.axisX(self.serie_order).setMin(1)
        self.chart.axisX(self.serie_current).setTickInterval(1)

        self.chart.axisY(self.serie_current).setMin(1)
        self.chart.axisY(self.serie_order).setMin(1)
        self.chart.axisY(self.serie_current).setMax(self.default_range_max_y)
        self.chart.axisY(self.serie_order).setMax(self.default_range_max_y)

        self.chart_view.setChart(self.chart)

        self.recalculate_range_x()

    @qtSlot(int)
    def slider_changed(self, value: int):
        """
        Qt Slot

        Function called when the scrollbar and zoom has changed.
        """
        self.recalculate_range_x()

    def recalculate_range_x(self):
        """
        Given the current zoom and current position of the scrollbar,
        compute the X min/max range and the slider position.
        """
        if self.slider_events_disabled:
            return
        self.slider_events_disabled = True

        span = int(self.range_max_x / self.zoom.value())
        span = span + span % 2
        scroll_min = span / 2
        scroll_max = self.range_max_x - span / 2

        scroll = self.scrollbar.value()
        scroll = max(scroll_min, scroll)
        scroll = min(scroll_max, scroll)

        self.scrollbar.setMinimum(scroll_min)
        self.scrollbar.setMaximum(scroll_max)
        self.scrollbar.setValue(scroll)

        self.chart.axisX(self.serie_current).setMax(self.range_max_x)
        self.chart.axisX(self.serie_order).setMax(self.range_max_x)

        span = int(self.range_max_x / self.zoom.sliderPosition())
        span = span + span % 2

        x_min = scroll - span / 2
        x_max = scroll + span / 2
        self.chart.axisX(self.serie_current).setRange(x_min, x_max)
        self.chart.axisX(self.serie_order).setRange(x_min, x_max)

        self.slider_events_disabled = False

    def reset(self):
        """
        Reset the chart
        """
        self.serie_current.clear()
        self.serie_order.clear()

        self.range_max_x = self.default_range_max_x
        self.range_max_y = self.default_range_max_y

        self.recalculate_range_x()

    def new_robot_state(
            self, mode: CtrlModeEnum, cycle: int,
            current: Optional[float], order: Optional[float]) -> None:
        """
        Add a new point on the chart view.

        Arguments:
            mode: Current mode
            cycle: Current cycle
            current: Current value
            order: Order value
        """
        if mode == CtrlModeEnum.STOP:
            self.need_reset = True
            return

        if self.need_reset:
            self.need_reset = False
            self.reset()

        self.range_max_x = max(self.range_max_x, cycle)

        if current:
            self.serie_current.append(cycle, current.distance)
            self.range_max_y = max(self.range_max_y, current.distance)

        if order:
            self.serie_order.append(cycle, order.distance)
            self.range_max_y = max(self.range_max_y, order.distance)

        self.chart.axisY(self.serie_current).setMax(self.range_max_y)
        self.chart.axisY(self.serie_order).setMax(self.range_max_y)

        self.recalculate_range_x()

    @qtSlot()
    def save_values(self):
        """
        Qt Slot

        Open a file dialog to select a file and save chart values in it.
        """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption=f"Select file to save {self.name} values",
            dir="",
            filter="CSV Files (*.csv)",
            # Workaround a know Qt bug
            options=QtWidgets.QFileDialog.DontUseNativeDialog
        )
        if filename:
            with Path(filename).open("w", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=["cycle", "order", "current"])
                writer.writeheader()

                for order, current in zip(self.serie_order.points(), self.serie_current.points()):
                    writer.writerow({"cycle": int(order.x()), "order": order.y(), "current": current.y()})


class ChartsView(QtWidgets.QDialog):
    """ChartsView class

    Build the calibration charts window.

    Attributes:
        saved_geometry: Saved window position
        closed: Qt signal emitted when the window is hidden
    """
    saved_geometry: QtCore.QRect = None
    closed: qtSignal = qtSignal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Calibration Charts")
        self.setModal(False)
        self.setMinimumSize(QtCore.QSize(400, 400))

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.linear_speed_chart = ChartView(self, "Linear Speed")
        self.layout.addWidget(self.linear_speed_chart, 0, 0)

    @qtSlot(RobotState)
    def new_robot_state(self, state: RobotState) -> None:
        """
        Qt Slot

        Send robot data to corresponding charts

        Arguments:
            state: New robot state
        """
        self.linear_speed_chart.new_robot_state(state.mode, state.cycle, state.speed_current, state.speed_order)

    def restore_saved_geometry(self):
        """
        Reuse the position of the last displayed property window for the current window.
        """
        if self.saved_geometry:
            self.setGeometry(self.saved_geometry)

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Hide the window.

        Arguments:
            event: The close event (unused)
        """
        self.saved_geometry = self.geometry()
        self.closed.emit()
        event.accept()

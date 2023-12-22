from typing import List

from PySide6 import QtCharts, QtCore, QtWidgets, QtGui
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from cogip.utils.lidartablemodel import LidarTableModel


class LidarView(QtWidgets.QWidget):
    """
    This class is a widget that provides the graphic view and instantiates the polar chart,
    sliders and the table view.

    Attributes:
        min_distance: min value of the distance range (use on the chart)
        max_distance: max value of the distance range (use on the chart)
        max_intensity: max value of the intensity range (use on the chart)
        enable_plain_area: whether to display a line or an plain area for distance values
        max_intensity_threshold: max value of the intensity threshold slider (max value for YGLidar G2)
        new_filer: Qt signal emitted when the filter value is modified
        new_intensity_threshold: Qt signal emitted when the filter intensity threshold is modified
    """
    min_distance: int = 100
    max_distance: int = 5000
    max_intensity: int = 1024
    enable_plain_area: bool = True
    max_intensity_threshold: int = 1024
    new_filter: qtSignal(int) = qtSignal(int)
    new_intensity_threshold: qtSignal(int) = qtSignal(int)
    nb_angles: int = 360

    def __init__(
            self,
            table_model: LidarTableModel,
            angle_values: List[int],
            distance_values: List[int],
            intensity_values: List[int],
            distance_color: QtGui.QColor,
            intensity_color: QtGui.QColor,
            nb_angles: int,
            parent: QtWidgets.QWidget | None = None):
        """
        Class constructor.

        Arguments:
            table_model: table model object
            angle_values: angle values list
            distance_values: distance values list
            intensity_values: intensity values list
            distance_color: distance color
            intensity_color: intensity color
            nb_angles: number of angles
            parent: The parent widget
        """
        super().__init__(parent)

        self.table_model = table_model
        self.angle_values = angle_values
        self.distance_values = distance_values
        self.intensity_values = intensity_values
        self.distance_color = distance_color
        self.intensity_color = intensity_color
        self.nb_angles = nb_angles

        self.first_index = self.table_model.createIndex(0, 1)
        self.last_index = self.table_model.createIndex(self.nb_angles - 1, 2)

        layout = QtWidgets.QHBoxLayout(self)

        chart_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(chart_layout)

        # Create polar chart and chart view
        self.chart = QtCharts.QPolarChart()
        self.chart.setTitle("Lidar Data")
        self.chart.setMinimumSize(QtCore.QSize(800, 800))
        self.chart_view = QtCharts.QChartView(self.chart)
        self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        chart_layout.addWidget(self.chart_view)

        # Add axis
        self.degree_axis = QtCharts.QValueAxis(self.chart)
        self.degree_axis.setRange(-180, 179)
        self.degree_axis.setLabelFormat("%d")
        self.degree_axis.setTickCount(17)
        self.degree_axis.setMinorTickCount(1)
        self.chart.addAxis(self.degree_axis, QtCharts.QPolarChart.PolarOrientationAngular)

        self.distance_axis = QtCharts.QValueAxis(self.chart)
        self.distance_axis.setRange(0, self.max_distance)
        self.distance_axis.setMinorTickCount(2)
        self.distance_axis.setTickCount(26)
        self.distance_axis.setTickAnchor(1)
        self.distance_axis.setLabelFormat("%d")
        self.chart.addAxis(self.distance_axis, QtCharts.QPolarChart.PolarOrientationRadial)

        self.intensity_axis = QtCharts.QValueAxis(self.chart)
        self.intensity_axis.setRange(0, self.max_intensity)
        self.intensity_axis.setLabelFormat("%d")
        self.intensity_axis.setLabelsVisible(False)
        self.chart.addAxis(self.intensity_axis, QtCharts.QPolarChart.PolarOrientationRadial)

        # Add series
        self.distance_serie = QtCharts.QLineSeries(name="Distance")
        # self.distance_serie.replace([QtCore.QPointF(i, 0) for i in range(self.nb_angles)])
        if self.enable_plain_area:
            self.center_serie = QtCharts.QLineSeries()
            # self.center_serie.replace([QtCore.QPointF(i, 0) for i in range(self.nb_angles)])
            self.distance_area_serie = QtCharts.QAreaSeries(
                self.distance_serie, self.center_serie, name="Distance"
            )
            self.chart.addSeries(self.distance_area_serie)
            self.distance_area_serie.attachAxis(self.degree_axis)
            self.distance_area_serie.attachAxis(self.distance_axis)
        else:
            self.chart.addSeries(self.distance_serie)
            self.distance_serie.attachAxis(self.degree_axis)
            self.distance_serie.attachAxis(self.distance_axis)

        self.intensity_serie = QtCharts.QLineSeries(name="Intensity")
        # self.intensity_serie.replace([QtCore.QPointF(i, 0) for i in range(self.nb_angles)])
        self.chart.addSeries(self.intensity_serie)
        self.intensity_serie.attachAxis(self.degree_axis)
        self.intensity_serie.attachAxis(self.intensity_axis)

        # Add a grid for sliders
        sliders_layout = QtWidgets.QGridLayout()
        sliders_layout.setColumnStretch(0, 1)
        sliders_layout.setColumnStretch(1, 10)
        sliders_layout.setColumnStretch(2, 10)
        sliders_layout.setColumnStretch(3, 200)
        chart_layout.addLayout(sliders_layout)

        # Distance Zoom slider
        distance_label = QtWidgets.QLabel("Max Distance:")
        sliders_layout.addWidget(distance_label, 0, 1)
        self.distance_value = QtWidgets.QLabel()
        sliders_layout.addWidget(self.distance_value, 0, 2)
        distance_zoom = QtWidgets.QSlider(
            QtCore.Qt.Horizontal, minimum=-self.max_distance, maximum=-self.min_distance
        )
        distance_zoom.valueChanged.connect(self.distance_zoom_changed)
        distance_zoom.setValue(-self.max_distance)
        distance_zoom.setStyleSheet(
            "QSlider::handle:horizontal {"
            "    border-radius: 5px; border: 2px solid #FFFFFF; width: 20px; margin: -5px 0;"
            f"   background: {hex(self.distance_color.rgb()).replace('0x', '#')}"
            "}"
            "QSlider::sub-page:horizontal {"
            f"   background: {hex(self.distance_color.rgb()).replace('0x', '#')};"
            "}"
        )
        sliders_layout.addWidget(distance_zoom, 0, 3)

        # Intensity Zoom slider
        intensity_label = QtWidgets.QLabel("Max Intensity:")
        sliders_layout.addWidget(intensity_label, 1, 1)
        self.intensity_value = QtWidgets.QLabel()
        sliders_layout.addWidget(self.intensity_value, 1, 2)
        intensity_zoom = QtWidgets.QSlider(QtCore.Qt.Horizontal, minimum=-self.max_intensity, maximum=0)
        intensity_zoom.valueChanged.connect(self.intensity_zoom_changed)
        intensity_zoom.setValue(-self.max_intensity)
        intensity_zoom.setStyleSheet(
            "QSlider::handle:horizontal {"
            "    border-radius: 5px; border: 2px solid #FFFFFF; width: 20px; margin: -5px 0;"
            f"   background: {hex(self.intensity_color.rgb()).replace('0x', '#')};"
            "}"
            "QSlider::sub-page:horizontal {"
            f"   background: {hex(self.intensity_color.rgb()).replace('0x', '#')};"
            "}"
        )
        sliders_layout.addWidget(intensity_zoom, 1, 3)

        # Distance filter slider
        filter_check = QtWidgets.QCheckBox()
        filter_check.stateChanged.connect(self.filter_check_changed)
        sliders_layout.addWidget(filter_check, 2, 0)
        self.filter_label = QtWidgets.QLabel("Distance filter:")
        sliders_layout.addWidget(self.filter_label, 2, 1)
        self.filter_value = QtWidgets.QLabel()
        sliders_layout.addWidget(self.filter_value, 2, 2)
        self.filter_slider = QtWidgets.QSlider(
            QtCore.Qt.Horizontal, minimum=self.min_distance, maximum=self.max_distance
        )
        self.filter_slider.valueChanged.connect(self.filter_slider_changed)
        self.filter_slider.setValue(500)
        sliders_layout.addWidget(self.filter_slider, 2, 3)

        filter_check.setChecked(False)
        self.filter_value.setEnabled(False)
        self.filter_slider.setEnabled(False)

        # Intensity threshold slider
        self.intensity_threshold_label = QtWidgets.QLabel("Intensity threshold:")
        sliders_layout.addWidget(self.intensity_threshold_label, 3, 1)
        self.intensity_threshold_value = QtWidgets.QLabel()
        sliders_layout.addWidget(self.intensity_threshold_value, 3, 2)
        self.intensity_threshold_slider = QtWidgets.QSlider(
            QtCore.Qt.Horizontal, minimum=0, maximum=self.max_intensity_threshold
        )
        self.intensity_threshold_slider.valueChanged.connect(self.intensity_threshold_slider_changed)
        self.intensity_threshold_slider.setValue(0)
        sliders_layout.addWidget(self.intensity_threshold_slider, 3, 3)

        # Create the table view
        table_view = QtWidgets.QTableView()
        table_view.setModel(self.table_model)
        table_view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table_view.resizeColumnsToContents()
        table_view.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        layout.addWidget(table_view)

    @qtSlot(int)
    def distance_zoom_changed(self, value: int):
        """
        Qt Slot

        Function called when the distance zoom slider has changed.

        Arguments:
            value: new value
        """
        self.distance_axis.setMax(-value)
        self.distance_value.setText(str(-value))

    @qtSlot(int)
    def intensity_zoom_changed(self, value: int):
        """
        Qt Slot

        Function called when the intensity zoom slider has changed.

        Arguments:
            value: new value
        """
        self.intensity_axis.setMax(-value)
        self.intensity_value.setText(str(-value))

    @qtSlot(int)
    def filter_slider_changed(self, value: int):
        """
        Qt Slot

        Function called when the filter value slider has changed.

        Arguments:
            value: new value
        """
        self.filter_value.setText(str(value))
        self.new_filter.emit(value)

    @qtSlot(int)
    def filter_check_changed(self, state: int):
        """
        Qt Slot

        Function called when the filter checkbox is checked/unchecked.

        Arguments:
            state: new state
        """
        enabled = state != 0
        self.filter_value.setEnabled(enabled)
        self.filter_slider.setEnabled(enabled)

        self.new_filter.emit(self.filter_slider.value() if enabled else 0)

    @qtSlot(int)
    def intensity_threshold_slider_changed(self, value: int):
        """
        Qt Slot

        Function called when the intensity threshold value slider has changed.

        Arguments:
            value: new value
        """
        self.intensity_threshold_value.setText(str(value))
        self.new_intensity_threshold.emit(value)

    @qtSlot()
    def update_data(self) -> None:
        """
        Qt Slot

        Function called to update data on chart and table.
        """
        self.table_model.dataChanged.emit(self.first_index, self.last_index, [QtCore.Qt.DisplayRole])

        self.distance_serie.replace([
            QtCore.QPointF(angle, value) for angle, value in zip(self.angle_values, self.distance_values)
        ])
        self.intensity_serie.replace([
            QtCore.QPointF(angle, value) for angle, value in zip(self.angle_values, self.intensity_values)
        ])

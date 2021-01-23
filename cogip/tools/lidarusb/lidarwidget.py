from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import Slot as qtSlot

from cogip.tools.lidarusb import datastruct
from cogip.tools.lidarusb.tablemodel import TableModel


class LidarWidget(QtWidgets.QWidget):
    """
    This class is a widget that provides the graphic view and instantiates the polar chart,
    sliders and the table view.

    Attributes:
        min_distance: min value of the distance range (use on the chart)
        max_distance: max value of the distance range (use on the chart)
        max_intensity: max value of the intensity range (use on the chart)
        enable_plain_area: whether to display a line or an plain area for distance values
    """
    min_distance: int = 100
    max_distance: int = 5000
    max_intensity: int = 12000
    enable_plain_area: bool = True

    def __init__(self, parent=None):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
        """
        super().__init__(parent)
        self.lidar_data = datastruct.LidarData()

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
        self.degree_axis.setRange(0, 360)
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
        self.distance_serie.replace([QtCore.QPointF(i, 0) for i in range(360)])
        if self.enable_plain_area:
            self.center_serie = QtCharts.QLineSeries()
            self.center_serie.replace([QtCore.QPointF(i, 0) for i in range(360)])
            self.distance_area_serie = QtCharts.QAreaSeries(
                self.distance_serie, self.center_serie, name="Distance"
            )
            self.chart.addSeries(self.distance_area_serie)
            self.distance_area_serie.attachAxis(self.degree_axis)
            self.distance_area_serie.attachAxis(self.distance_axis)
            distance_color = self.distance_area_serie.color()
        else:
            self.chart.addSeries(self.distance_serie)
            self.distance_serie.attachAxis(self.degree_axis)
            self.distance_serie.attachAxis(self.distance_axis)
            distance_color = self.distance_serie.color()

        self.intensity_serie = QtCharts.QLineSeries(name="Intensity")
        self.intensity_serie.replace([QtCore.QPointF(i, 0) for i in range(360)])
        self.chart.addSeries(self.intensity_serie)
        self.intensity_serie.attachAxis(self.degree_axis)
        self.intensity_serie.attachAxis(self.intensity_axis)
        intensity_color = self.intensity_serie.pen().color()

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
            f"   background: {hex(distance_color.rgb()).replace('0x', '#')}"
            "}"
            "QSlider::sub-page:horizontal {"
            f"   background: {hex(distance_color.rgb()).replace('0x', '#')};"
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
            f"   background: {hex(intensity_color.rgb()).replace('0x', '#')};"
            "}"
            "QSlider::sub-page:horizontal {"
            f"   background: {hex(intensity_color.rgb()).replace('0x', '#')};"
            "}"
        )
        sliders_layout.addWidget(intensity_zoom, 1, 3)

        # Distance filter slider
        filter_check = QtWidgets.QCheckBox()
        filter_check.setChecked(True)
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

        # Create the table model
        self.table_model = TableModel(self.lidar_data, distance_color, intensity_color)

        # Create the table view
        table_view = QtWidgets.QTableView()
        table_view.setModel(self.table_model)
        table_view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table_view.resizeColumnsToContents()
        table_view.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        layout.addWidget(table_view)

        # ** Don't use MVC for charts since it is not fast enough
        # ** (keep code in comments because it is still interesting for later use)
        # distance_mapper = QtCharts.QVXYModelMapper(self)
        # distance_mapper.setXColumn(0)
        # distance_mapper.setYColumn(1)
        # distance_mapper.setSeries(self.distance_serie)
        # distance_mapper.setModel(self.table_model)

        # intensity_mapper = QtCharts.QVXYModelMapper(self)
        # intensity_mapper.setXColumn(0)
        # intensity_mapper.setYColumn(2)
        # intensity_mapper.setSeries(self.intensity_serie)
        # intensity_mapper.setModel(self.table_model)

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
        self.lidar_data.filter_value = value

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
        if enabled:
            self.lidar_data.filter_value = self.filter_slider.value()
        else:
            self.lidar_data.filter_value = 0

    @qtSlot(bytes)
    def new_frame(self, frame_bytes: bytes) -> None:
        """
        Qt Slot

        Function called when a new frame is available.

        Arguments:
            frame_bytes: new frame data
        """
        frame_data = datastruct.FrameData.from_buffer_copy(frame_bytes)

        # Update frame in Lidar data
        self.lidar_data.set_frame(frame_data.index, frame_data)
        angle_start = frame_data.index * 6

        # Update table
        index1 = self.table_model.createIndex(angle_start, 1)
        index2 = self.table_model.createIndex(angle_start + 6, 2)
        self.table_model.dataChanged.emit(index1, index2, [QtCore.Qt.DisplayRole])

        # Update chart (the full chart at once when all frames are updated)
        if frame_data.index == 59:
            self.distance_serie.replace(self.lidar_data.get_distance_points())
            self.intensity_serie.replace(self.lidar_data.get_intensity_points())

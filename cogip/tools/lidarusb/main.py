#!/usr/bin/env python3

import sys
from threading import Thread

from PySide6 import QtWidgets, QtGui
import typer

from cogip.utils.lidartablemodel import LidarTableModel
from cogip.widgets.lidarview import LidarView

from .dataproxy import DataProxy
from .lidar import Lidar
from .mainwindow import MainWindow


def main_opt(nb_angles: int = 360):  # 420, 724, 1020
    distance_color = QtGui.QColor.fromRgbF(0.125490, 0.623529, 0.874510, 1.000000)
    intensity_color = QtGui.QColor.fromRgbF(0.600000, 0.792157, 0.325490, 1.000000)

    angle_values = [0 for i in range(nb_angles)]
    distance_values = [0 for i in range(nb_angles)]
    intensity_values = [0 for i in range(nb_angles)]

    table_model = LidarTableModel(
        angle_values, distance_values, intensity_values,
        distance_color, intensity_color, nb_angles
    )

    data_proxy = DataProxy(angle_values, distance_values, intensity_values)

    # Create Lidar object
    lidar = Lidar()

    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Create main widget
    lidar_view = LidarView(
        table_model,
        angle_values, distance_values, intensity_values,
        distance_color, intensity_color,
        nb_angles
    )

    # Create main window
    main_window = MainWindow(lidar_view)

    # Connect signals and slots
    lidar_view.new_filter.connect(data_proxy.set_filter)
    lidar_view.new_intensity_threshold.connect(lidar.set_intensity_threshold)
    lidar.signal_new_data.connect(data_proxy.new_data)
    data_proxy.update_data.connect(lidar_view.update_data)

    # Show UI
    main_window.show()

    # Create lidar thread and start it
    controller_thread = Thread(target=lidar.process_points)
    controller_thread.start()

    ret = app.exec_()

    lidar.quit()
    controller_thread.join()

    sys.exit(ret)


def main():
    """
    Starts the Lidar USB View tool.

    During installation of the simulation tools, `setuptools` is configured
    to create the `lidarusb` script using this function as entrypoint.
    """
    typer.run(main_opt)

#!/usr/bin/env python3

import sys
from threading import Thread

from PySide2 import QtWidgets, QtGui
import serial.tools.list_ports
import typer

from cogip import logger
from cogip.config import settings
from cogip.tools.lidarpf.dataproxy import DataProxy
from cogip.tools.lidarpf.lidarserial import LidarSerial
from cogip.tools.lidarpf.mainwindow import MainWindow
from cogip.utils.lidartablemodel import LidarTableModel
from cogip.widgets.lidarview import LidarView


def get_default_uart() -> str:
    """
    Detect all serial ports and return the first one as the default port.
    If no port is found, return the default port from global settings.
    """
    uart = settings.default_uart
    comports = serial.tools.list_ports.comports()
    if len(comports) > 0:
        uart = comports[0].device
    logger.info(f"Using default UART: {uart}")
    return uart


def main_opt(uart: str = typer.Argument(get_default_uart, help="The UART port to use")):
    distance_color = QtGui.QColor.fromRgbF(0.125490, 0.623529, 0.874510, 1.000000)
    intensity_color = QtGui.QColor.fromRgbF(0.600000, 0.792157, 0.325490, 1.000000)

    distance_values = [0 for i in range(360)]
    intensity_values = [0 for i in range(360)]

    table_model = LidarTableModel(distance_values, intensity_values, distance_color, intensity_color)

    data_proxy = DataProxy(distance_values, intensity_values)

    # Create controller
    controller = LidarSerial(uart)

    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Create main widget
    lidar_view = LidarView(
        table_model,
        distance_values, intensity_values,
        distance_color, intensity_color
    )

    # Create main window
    main_window = MainWindow(lidar_view)

    # Connect signals and slots
    main_window.start_action.triggered.connect(controller.start_lidar)
    main_window.pause_action.triggered.connect(controller.stop_lidar)
    lidar_view.new_filter.connect(controller.set_filter)
    controller.new_data.connect(data_proxy.new_data)
    data_proxy.update_data.connect(lidar_view.update_data)

    # Show UI
    main_window.show()

    # Create controller thread and start it
    # (open serial port)
    controller_thread = Thread(target=controller.process_output)
    controller_thread.start()

    ret = app.exec_()

    controller.quit()
    controller_thread.join()

    sys.exit(ret)


def main():
    """
    Starts the Lidar Platform View tool.

    During installation of the simulation tools, `setuptools` is configured
    to create the `lidarpf` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == '__main__':
    main()

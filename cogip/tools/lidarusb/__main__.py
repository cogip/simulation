#!/usr/bin/env python3

import sys
from threading import Thread

from PySide2 import QtWidgets
import serial.tools.list_ports
import typer

from cogip import logger
from cogip.config import settings
from cogip.tools.lidarusb.lidarserial import LidarSerial
from cogip.tools.lidarusb.lidarwidget import LidarWidget


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
    # Create controller
    controller = LidarSerial(uart)

    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Create UI
    main_window = QtWidgets.QMainWindow()
    main_window.setWindowTitle("Lidar USB Viewer")
    lidar_widget = LidarWidget()
    main_window.setCentralWidget(lidar_widget)

    # Connect signals and slots
    controller.new_frame.connect(lidar_widget.new_frame)

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
    Starts the Lidar USB View tool.

    During installation of the simulation tools, `setuptools` is configured
    to create the `lidarusb` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import argparse
import faulthandler
from pathlib import Path
import psutil
from queue import Queue
import shutil
import subprocess
import sys
from threading import Thread

import serial.tools.list_ports
# import ptvsd
from PySide2 import QtWidgets

from cogip import logger
from cogip.config import settings
from cogip.mainwindow import MainWindow
from cogip.serialcontroller import SerialController
from cogip.gameview import GameView
from cogip.assetentity import AssetEntity
from cogip.robotentity import RobotEntity


def get_argument_parser(default_uart: str = "/tmp/ptsCOGIP"):
    arg_parser = argparse.ArgumentParser(description='Launch COGIP Simulator.')
    iodevice_group = arg_parser.add_mutually_exclusive_group()
    iodevice_group.add_argument(
        "-D", "--device",
        dest="uart_device", default=default_uart,
        help="Specify UART device"
    )
    iodevice_group.add_argument(
        "-B", "--binary",
        dest="native_binary", default=settings.native_binary,
        help="Specify native board binary compiled in calibration mode"
    )
    return arg_parser


def main():
    faulthandler.enable()

    # Virtual uart for native simulation
    virtual_uart = settings.default_uart

    # Run native mode by default
    # Real mode used by default if an uart is found, use the first uart discovered
    default_uart = virtual_uart
    logger.info("Discovering uarts:")
    for info in serial.tools.list_ports.comports():
        logger.info(f"  - {info.device}:")
        if default_uart == virtual_uart:
            default_uart = info.device

    if default_uart != virtual_uart:
        logger.info(f"Default uart: {default_uart}")

    # Parse command line arguments
    arg_parser = get_argument_parser(default_uart)
    args = arg_parser.parse_args()

    # Start socat redirecting native process stdin/stdout to virtual uart
    if args.uart_device != virtual_uart:
        socat_process = None
    else:
        socat_path = shutil.which("socat")
        if not socat_path:
            logger.error("'socat' not found.")
            sys.exit(1)
        socat_args = [
            socat_path,
            # "-v",
            # "-v",
            f'PTY,link={virtual_uart},rawer,wait-slave',
            f'EXEC:"{args.native_binary}"'
        ]
        logger.info(f"Execute: {' '.join(socat_args)}")
        socat_process = subprocess.Popen(socat_args, executable=socat_path)

    position_queue = Queue()

    # Create controller
    controller = SerialController(args.uart_device, position_queue)

    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Create UI
    win = MainWindow()

    # Create game view
    game_view = GameView()
    win.setCentralWidget(game_view)

    # Create table entity
    table_entity = AssetEntity(
        asset_path=Path(settings.table_filename).resolve(),
        asset_name="Table2019"
    )
    game_view.add_asset(table_entity)

    # Create robot entity
    robot_entity = RobotEntity(
        asset_path=Path(settings.robot_filename).resolve(),
        asset_name="Robot2019_Simu"
    )
    game_view.add_asset(robot_entity)

    # Connect UI signals to Controller slots
    win.signal_send_command.connect(controller.slot_new_command)

    # Connect UI signals to GameView slots
    win.signal_add_obstacle.connect(game_view.add_obstacle)

    # Connect Controller signals to Robot slots
    controller.signal_new_robot_position.connect(robot_entity.set_position)
    controller.signal_new_dyn_obstacles.connect(robot_entity.set_dyn_obstacles)

    # Connect Controller signals to UI slots
    controller.signal_new_console_text.connect(win.log_text.append)
    controller.signal_new_menu.connect(win.load_menu)
    controller.signal_new_robot_position.connect(win.new_robot_position)

    # Show UI
    win.show()
    # win.showFullScreen()
    win.raise_()

    # Create controller thread and start it
    # (open serial port)
    controller_thread = Thread(target=controller.process_output)
    controller_thread.start()

    ret = app.exec_()

    controller.quit()
    controller_thread.join()

    if socat_process:
        socat_process.kill()

        # Kill all remaining bin instance
        for proc in psutil.process_iter(attrs=['exe']):
            if proc.info['exe'] == args.native_binary:
                proc.kill()

    sys.exit(ret)


if __name__ == '__main__':
    main()

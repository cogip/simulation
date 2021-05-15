#!/usr/bin/env python3

import argparse
import faulthandler
from pathlib import Path
import psutil
import shutil
import subprocess
import sys
from threading import Thread

import serial.tools.list_ports
# import ptvsd
from PySide2 import QtWidgets, QtGui

from cogip import logger
from cogip.config import settings
from cogip.entities.asset import AssetEntity
from cogip.entities.robot import RobotEntity

from .mainwindow import MainWindow
from .serialcontroller import SerialController


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
        dest="native_binary", default=settings.native_binary, type=Path,
        help="Specify native binary compiled with shell menus enabled"
    )
    iodevice_group.add_argument(
        "-r", "--remote",
        dest="remote", default=None,
        help="Remote device providing the serial port connected to the robot"
    )
    arg_parser.add_argument(
        "-n", "--no-wait",
        dest="no_wait", action='store_true',
        help="Do not wait for the firmware start sequence"
    )
    return arg_parser


def main():
    """
    Starts the simulator.

    During installation of the simulation tools, `setuptools` is configured
    to create the `simulator` script using this function as entrypoint.
    """
    faulthandler.enable()

    # Virtual uart for native simulation
    virtual_uart = settings.default_uart

    # Run native mode by default
    default_uart = virtual_uart

    if "-B" not in sys.argv and "--binary" not in sys.argv:
        # Real mode used by default if an uart is found,
        # and if native firmware is not explicitly provided
        # Use the first uart discovered
        logger.info("Discovering uarts:")
        for info in serial.tools.list_ports.comports():
            logger.info(f"  - {info.device}:")
            if default_uart == virtual_uart:
                default_uart = info.device

    logger.info(f"Using uart: {default_uart}")

    # Parse command line arguments
    arg_parser = get_argument_parser(default_uart)
    args = arg_parser.parse_args()

    # Start socat redirecting native process stdin/stdout to virtual uart
    socat_process = None
    if args.uart_device == virtual_uart:
        socat_path = shutil.which("socat")
        if not socat_path:
            logger.error("'socat' not found.")
            sys.exit(1)

        if args.remote:
            picocom_path = shutil.which("picocom")
            if not picocom_path:
                logger.error("'picocom' not found.")
                sys.exit(1)

            socat_args = [
                socat_path,
                f'PTY,link={virtual_uart},rawer,wait-slave',
                f'EXEC:"ssh {args.remote} {picocom_path} -q --imap lfcrlf -b 115200 /dev/ttyACM0"'
            ]
        else:
            if not args.native_binary.exists():
                logger.error(f"'{args.native_binary}' not found.")
                sys.exit(1)
            if not args.native_binary.is_file():
                logger.error(f"'{args.native_binary}' is not a file.")
                sys.exit(1)

            socat_args = [
                socat_path,
                f'PTY,link={virtual_uart},rawer,wait-slave',
                f'EXEC:"{args.native_binary.resolve()}"'
            ]

        logger.info(f"Execute: {' '.join(socat_args)}")
        socat_process = subprocess.Popen(socat_args, executable=socat_path)

    # Create controller
    controller = SerialController(args.uart_device, no_wait=args.no_wait)

    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Create UI
    win = MainWindow()

    # Create table entity
    table_entity = AssetEntity(
        asset_path=Path(settings.table_filename).resolve(),
        asset_name="Table2019"
    )
    win.game_view.add_asset(table_entity)

    # Create robot entity
    robot_entity = RobotEntity(
        asset_path=Path(settings.robot_filename).resolve(),
        asset_name="Robot2019"
    )
    win.game_view.add_asset(robot_entity)

    # Create robot entity
    robot_final_entity = RobotEntity(
        asset_path=Path(settings.robot_filename).resolve(),
        asset_name="Robot2019",
        enable_tof_sensors=False,
        enable_lidar_sensors=False,
        color=QtGui.QColor.fromRgb(0, 255, 0, 50)
    )
    win.game_view.add_asset(robot_final_entity)

    # Connect UI signals to Controller slots
    win.signal_send_command.connect(controller.new_command)

    # Connect UI signals to GameView slots
    win.signal_add_obstacle.connect(win.game_view.add_obstacle)
    win.signal_load_obstacles.connect(win.game_view.load_obstacles)
    win.signal_save_obstacles.connect(win.game_view.save_obstacles)

    # Connect Controller signals to Robot slots
    controller.signal_new_robot_state.connect(robot_entity.new_robot_state)
    controller.signal_new_robot_state.connect(robot_final_entity.new_robot_state)
    controller.signal_new_dyn_obstacles.connect(robot_entity.set_dyn_obstacles)

    # Connect Controller signals to UI slots
    controller.signal_new_console_text.connect(win.log_text.append)
    controller.signal_new_menu.connect(win.load_menu)
    controller.signal_new_robot_state.connect(win.new_robot_state)

    # Connect Controller signals to ChartsView slots
    controller.signal_new_robot_state.connect(win.charts_view.new_robot_state)

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

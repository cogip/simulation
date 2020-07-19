#!/usr/bin/env python3

import os
import sys
import re
import math
import ptvsd
import argparse
import shutil
import dotenv
import subprocess
import psutil
import serial.tools.list_ports
from pathlib import Path
from queue import Queue
from threading import Thread

from PyQt5 import QtCore, QtWidgets

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), verbose=False)

if '__file__' in locals():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cogip import logger
from cogip.config import Config
from cogip.table import Table
from cogip.robot import Robot
from cogip.mainwindow import MainWindow
from cogip.automaton import Automaton
from cogip.serialcontroller import SerialController

import faulthandler

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
        dest="native_binary", default=Config.NATIVE_BINARY,
        help="Specify native board binary compiled in calibration mode"
    )
    return arg_parser

if __name__ == '__main__':
    faulthandler.enable()

    # Virtual uart for native simulation
    virtual_uart = Config.DEFAULT_UART

    # Run native mode by default
    # Real mode used by default if an uart is found, use the first uart discovered 
    default_uart = virtual_uart
    logger.info(f"Discovering uarts:")
    for info in serial.tools.list_ports.comports():
        logger.info(f"  - {info.device()}:")
        if default_uart == virtual_uart:
            default_uart = info.device()
    else:
        logger.info("  - no port found")

    if default_uart != virtual_uart:
        logger.info(f"Default uart: {default_uart}")

    # Parse command line arguments
    arg_parser = get_argument_parser(default_uart)
    args = arg_parser.parse_args()

    # Start socat redirecting native process stdin/stdout to virtual uart
    if args.uart_device != virtual_uart:
        socat_process = None
    else:
        socat_path = shutil.which("socat")
        if not socat_path:
            logger.error("'socat' not found.")
            sys.exit(1)
        socat_args = [
            socat_path,
            #"-v",
            #"-v",
            f'PTY,link={virtual_uart},rawer,wait-slave',
            f'EXEC:"{args.native_binary}"'
        ]
        logger.info(f"Execute: {' '.join(socat_args)}")
        socat_process = subprocess.Popen(socat_args, executable=socat_path)

    position_queue = Queue()

    # Models must be loaded before QApplication init
    table = Table(Config.TABLE_FILENAME)
    robot = Robot(Config.ROBOT_FILENAME, position_queue)

    # Create automaton
    automaton = Automaton()

    # Create controller
    controller = SerialController(args.uart_device, position_queue)

    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Create UI
    win = MainWindow()

    # Add models to UI
    table.set_display(win.viewer._display)
    robot.set_display(win.viewer._display)

    # Connect Robot signals to UI slots
    robot.signal_position_updated.connect(win.new_robot_position)

    # Connect UI signals to Automaton slots
    win.trigger_signal.connect(automaton.new_trigger)

    # Connect Controller signals to Automaton slots
    controller.signal_new_trigger.connect(automaton.new_trigger)

    # Connect Automaton signals to Controller slots
    automaton.signal_enter_new_state.connect(controller.slot_send_command)

    # Connect Automaton signals to UI slots
    automaton.signal_new_state.connect(win.new_controller_state)

    # Connect Controller signals to UI slots
    controller.signal_new_console_text.connect(win.log_text.append)
    controller.signal_new_robot_position_number.connect(win.pos_nb_text.setText)

    # Move Robot to thread and start
    robot_thread = Thread(target=robot.update_position, daemon=True)
    robot_thread.start()

    # Show UI
    win.show()
    win.raise_()

    # Create controller thread and start it
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

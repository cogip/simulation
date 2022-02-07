#!/usr/bin/env python3
# flake8: noqa: E402
import faulthandler
import os
import sys

# Remove info logs from QWebEngineView.
# This needs to be set in os.environ before importing typer.
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.webenginecontext.info=false"

from PySide6 import QtWidgets
import typer

from cogip.entities.robot import RobotEntity
from cogip.entities.table import TableEntity

from .mainwindow import MainWindow
from .socketiocontroller import SocketioController


def main_opt(
        url: str = typer.Argument(
            "http://copilot",
            envvar="COPILOT_URL",
            help="URL to Copilot socket.io/web server")) -> None:
    """
    Launch COGIP Monitor.
    """
    faulthandler.enable()

    # Create socketio controller
    controller = SocketioController(url)

    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Create UI
    win = MainWindow(url)

    # Create table entity
    table_entity = TableEntity(win.game_view.root_entity)
    win.game_view.add_asset(table_entity)

    # Create robot entity
    robot_entity = RobotEntity()
    win.game_view.add_asset(robot_entity)

    # Connect UI signals to Controller slots
    win.signal_send_command.connect(controller.new_command)

    # Connect UI signals to GameView slots
    win.signal_add_obstacle.connect(win.game_view.add_obstacle)
    win.signal_load_obstacles.connect(win.game_view.load_obstacles)
    win.signal_save_obstacles.connect(win.game_view.save_obstacles)
    win.signal_load_samples.connect(win.game_view.load_samples)
    win.signal_save_samples.connect(win.game_view.save_samples)

    # Connect Controller signals to Robot slots
    controller.signal_new_robot_state.connect(robot_entity.new_robot_state)
    controller.signal_new_robot_state.connect(win.game_view.new_robot_state)

    # Connect Controller signals to UI slots
    controller.signal_new_console_text.connect(win.log_text.append)
    controller.signal_new_menu.connect(win.load_menu)
    controller.signal_new_robot_state.connect(win.new_robot_state)
    controller.signal_connected.connect(win.connected)

    # Connect Controller signals to ChartsView slots
    controller.signal_new_robot_state.connect(win.charts_view.new_robot_state)

    # Show UI
    win.show()
    # win.showFullScreen()
    win.raise_()

    controller.start()

    ret = app.exec_()

    controller.stop()

    sys.exit(ret)


def main():
    """
    Starts the copilot.

    During installation of the simulation tools, `setuptools` is configured
    to create the `copilot` script using this function as entrypoint.
    """
    typer.run(main_opt)

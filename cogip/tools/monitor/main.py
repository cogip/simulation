#!/usr/bin/env python3
# flake8: noqa: E402
import faulthandler
import os
import sys

# Remove info logs from QWebEngineView.
# This needs to be set in os.environ before importing typer.
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.webenginecontext.info=false"

from PySide6 import QtGui, QtWidgets
import typer

from cogip.entities.robot import RobotEntity
from cogip.entities.table import TableEntity

from .mainwindow import MainWindow
from .socketiocontroller import SocketioController


def main_opt(
        url: str = typer.Argument(
            "http://localhost:8080",
            envvar="COGIP_SERVER_URL",
            help="Server URL")) -> None:
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
    win.setWindowIcon(QtGui.QIcon("assets/cogip-logo.png"))

    # Create table entity
    table_entity = TableEntity()
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
    win.signal_load_cake_layers.connect(win.game_view.load_cake_layers)
    win.signal_save_cake_layers.connect(win.game_view.save_cake_layers)

    # Connect Controller signals to Robot slots
    controller.signal_new_robot_pose_current.connect(robot_entity.new_robot_pose_current)
    controller.signal_new_robot_pose_order.connect(robot_entity.new_robot_pose_order)
    controller.signal_new_robot_state.connect(win.game_view.new_robot_state)
    controller.signal_new_dyn_obstacles.connect(robot_entity.set_dyn_obstacles)
    controller.signal_start_lidar_emulation.connect(robot_entity.start_lidar_emulation)
    controller.signal_stop_lidar_emulation.connect(robot_entity.stop_lidar_emulation)
    robot_entity.lidar_emit_data_signal.connect(controller.emit_lidar_data)

    # Connect Controller signals to UI slots
    controller.signal_new_console_text.connect(win.log_text.append)
    controller.signal_new_menu.connect(win.load_menu)
    controller.signal_new_robot_pose_current.connect(win.new_robot_pose)
    controller.signal_new_robot_state.connect(win.new_robot_state)
    controller.signal_connected.connect(win.connected)
    controller.signal_exit.connect(win.close)

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

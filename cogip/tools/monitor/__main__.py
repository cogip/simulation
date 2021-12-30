#!/usr/bin/env python3
import faulthandler
import sys

# import ptvsd
from dotenv import load_dotenv
from PySide2 import QtWidgets
import typer

from cogip.entities.robot import RobotEntity, RobotShadowEntity
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
    win = MainWindow()

    # Create table entity
    table_entity = TableEntity(win.game_view.root_entity)
    win.game_view.add_asset(table_entity)

    # Create robot entity
    robot_entity = RobotEntity()
    win.game_view.add_asset(robot_entity)

    # Create robot entity
    robot_final_entity = RobotShadowEntity()
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
    load_dotenv()
    typer.run(main_opt)


if __name__ == '__main__':
    main()

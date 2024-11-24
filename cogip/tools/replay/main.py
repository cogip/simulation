#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Optional

import typer
from PySide6 import QtWidgets

from cogip import logger
from cogip.entities.robot import RobotEntity
from cogip.entities.table import TableEntity
from .mainwindow import MainWindow


def main_opt(trace_file: Optional[Path] = typer.Argument(None)):  # noqa
    """
    Starts replay.
    """

    if trace_file and not trace_file.is_file():
        logger.error(f"Error: '{trace_file}' is not a file or does not exist.")
        sys.exit(1)

    # Create QApplication
    app = QtWidgets.QApplication(sys.argv)

    # Create UI
    win = MainWindow(trace_file)

    # Create table entity
    table_entity = TableEntity(win.game_view.scene_entity)
    win.game_view.add_asset(table_entity)

    # Create robot entity
    robot_entity = RobotEntity()
    win.game_view.add_asset(robot_entity)

    # Connect UI signals
    win.signal_new_robot_state.connect(robot_entity.new_robot_state)
    win.signal_new_robot_state.connect(win.game_view.new_robot_state)
    win.signal_new_robot_state.connect(win.new_robot_state)
    win.signal_new_robot_state.connect(win.charts_view.new_robot_state)

    if trace_file:
        win.load_trace(trace_file)

    # Show UI
    win.show()
    # win.showFullScreen()
    win.raise_()

    sys.exit(app.exec_())


def main():
    """
    Starts the replay viewer.

    During installation of cogip-tools, `setuptools` is configured
    to create the `replay` script using this function as entrypoint.
    """
    typer.run(main_opt)

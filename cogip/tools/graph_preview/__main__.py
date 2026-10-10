#!/usr/bin/env python3
"""
CLI entry point for the graph preview tool.

Seeds a set of obstacles into its own shared memory segment, has the C++ graph library build a
visibility graph over them, and draws the raw obstacles, their inflated shapes and the graph. The
two parameters that shape the result are on sliders, so what a change does is something one watches
rather than infers.

Nothing else has to be running: the tool owns its segment.
"""

import logging
import os
import signal
import sys
from typing import Annotated

import typer
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication

from cogip.cpp.libraries.graph import GRAPH_CORNER_COUNT_MAX
from cogip.tools.graph_preview import logger
from cogip.tools.graph_preview.shared_memory import GraphPreviewMemory
from cogip.tools.graph_preview.window import GraphPreviewWindow
from cogip.tools.planner.table import TableEnum, get_table


def main_opt(
    *,
    corners: Annotated[
        int,
        typer.Option(
            "-n",
            "--corners",
            min=1,
            max=GRAPH_CORNER_COUNT_MAX,
            help="Number of sample points per rounded corner.",
            envvar="GRAPH_PREVIEW_CORNERS",
        ),
    ] = 6,
    inflation_radius: Annotated[
        float,
        typer.Option(
            "-r",
            "--inflation-radius",
            min=0.0,
            help="Radius added to every obstacle, mm. The robot shrunk to a point.",
            envvar="GRAPH_PREVIEW_INFLATION_RADIUS",
        ),
    ] = 150.0,
    clearance: Annotated[
        float,
        typer.Option(
            "-c",
            "--clearance",
            min=0.1,
            help="Distance every node keeps from the inflated shape, mm. Never zero.",
            envvar="GRAPH_PREVIEW_CLEARANCE",
        ),
    ] = 10.0,
    table: Annotated[
        TableEnum,
        typer.Option(
            "-t",
            "--table",
            help="Table to lay the obstacles on.",
            envvar="GRAPH_PREVIEW_TABLE",
        ),
    ] = TableEnum.Game,
    robot_id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=1,
            help="Robot ID. Decides which of this year's obstacles are on the table.",
            envvar=["ROBOT_ID"],
        ),
    ] = 1,
    table_margin: Annotated[
        float,
        typer.Option(
            "--table-margin",
            min=0.0,
            help="Margin taken off the table limits before nodes are filtered, mm.",
            envvar="GRAPH_PREVIEW_TABLE_MARGIN",
        ),
    ] = 0.0,
    shm_name: Annotated[
        str,
        typer.Option(
            "--shm-name",
            help="Shared memory segment to create. Its own, so it cannot collide with a robot's.",
            envvar="GRAPH_PREVIEW_SHM_NAME",
        ),
    ] = "cogip_graph_preview",
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages",
            envvar="GRAPH_PREVIEW_DEBUG",
        ),
    ] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)

    if os.getenv("QT_QPA_PLATFORM") is None:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QApplication(sys.argv)
    QtCore.QCoreApplication.setOrganizationName("cogip")
    QtCore.QCoreApplication.setApplicationName("COGIP Graph Preview")

    memory = GraphPreviewMemory(shm_name, get_table(table), table, robot_id, table_margin)
    window = GraphPreviewWindow(memory, corners, inflation_radius, clearance)

    # Let Ctrl+C through: the Qt event loop otherwise never gives Python a chance to run the
    # handler, and the segment would be left behind unlinked.
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    tick = QtCore.QTimer()
    tick.start(50)
    tick.timeout.connect(lambda: None)

    window.show()
    ret = app.exec()

    memory.close()
    sys.exit(ret)


def main():
    """
    Preview the visibility graph built over a set of obstacles.

    During installation of cogip-tools, a script called `cogip-graph-preview`
    will be created using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()

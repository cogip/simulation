#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path

import typer
from watchfiles import PythonFilter, run_process

from . import logger
from .avoidance import Avoidance


def changes_callback(changes):
    logger.info("Changes detected:", changes)


def run(*args, **kwargs) -> None:
    avoidance = Avoidance(*args, **kwargs)
    asyncio.run(avoidance.run())


def main_opt(
    server_url: str = typer.Option(
        "http://localhost:8080",
        help="Server URL",
        envvar="COGIP_SERVER_URL"
    ),
    id: int = typer.Option(
        1,
        "-i", "--id",
        min=1,
        help="Robot ID.",
        envvar=["ROBOT_ID", "AVOIDANCE_ID"]
    ),
    robot_width: int = typer.Option(
        225, min=100, max=1000,
        help="Width of the robot (in mm)",
        envvar="AVOIDANCE_ROBOT_WIDTH"
    ),
    obstacle_radius: int = typer.Option(
        150, min=50, max=500,
        help="Radius of a dynamic obstacle (in mm)",
        envvar="AVOIDANCE_OBSTACLE_RADIUS"
    ),
    obstacle_bb_margin: float = typer.Option(
        0.2, min=0, max=1,
        help="Obstacle bounding box margin in percent of the radius",
        envvar="AVOIDANCE_OBSTACLE_BB_MARGIN"
    ),
    obstacle_bb_vertices: int = typer.Option(
        6, min=3, max=20,
        help="Number of obstacle bounding box vertices",
        envvar="AVOIDANCE_OBSTACLE_BB_VERTICES"
    ),
    max_distance: int = typer.Option(
        2500, min=0, max=4000,
        help="Maximum distance to take avoidance points into account (mm)",
        envvar=["COGIP_MAX_DISTANCE", "AVOIDANCE_MAX_DISTANCE"]
    ),
    obstacle_sender_interval: float = typer.Option(
        0.2, min=0.1, max=2.0,
        help="Interval between each send of obstacles to dashboards (in seconds)",
        envvar="AVOIDANCE_OBSTACLE_SENDER_INTERVAL"
    ),
    path_refresh_interval: float = typer.Option(
        0.2, min=0.1, max=2.0,
        help="Interval between each update of robot paths (in seconds)",
        envvar="AVOIDANCE_PATH_REFRESH_INTERVAL"
    ),
    plot: bool = typer.Option(
        False,
        "-p", "--plot",
        help="Display avoidance graph in realtime",
        envvar=["AVOIDANCE_PLOT"]
    ),
    reload: bool = typer.Option(
        False,
        "-r", "--reload",
        help="Reload app on source file changes",
        envvar=["COGIP_RELOAD", "AVOIDANCE_RELOAD"]
    ),
    debug: bool = typer.Option(
        False,
        "-d", "--debug",
        help="Turn on debug messages",
        envvar=["COGIP_DEBUG", "AVOIDANCE_DEBUG"]
    )
):
    if debug:
        logger.setLevel(logging.DEBUG)

    args = (
        server_url,
        id,
        robot_width,
        obstacle_radius,
        obstacle_bb_margin,
        obstacle_bb_vertices,
        max_distance,
        obstacle_sender_interval,
        path_refresh_interval,
        plot,
        debug
    )

    if reload:
        watch_dir = Path(__file__).parent.parent.parent
        run_process(
            watch_dir,
            target=run,
            args=args,
            callback=changes_callback,
            watch_filter=PythonFilter(),
            debug=False
        )
    else:
        run(*args)


def main():
    """
    Launch COGIP Avoidance.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-avoidance` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == '__main__':
    main()

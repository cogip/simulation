#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path

import typer
from watchfiles import PythonFilter, run_process

from . import logger
from .planner import Planner


def changes_callback(changes):
    logger.info("Changes detected:", changes)


def run(*args, **kwargs) -> None:
    planner = Planner(*args, **kwargs)
    asyncio.run(planner.connect())


def main_opt(
    server_url: str = typer.Option(
        "http://localhost:8080",
        help="Server URL",
        envvar="COGIP_SERVER_URL"
    ),
    robot_width: int = typer.Option(
        225, min=100, max=1000,
        help="Width of the robot (in mm)",
        envvar="PLANNER_ROBOT_WIDTH"
    ),
    obstacle_radius: int = typer.Option(
        150, min=50, max=500,
        help="Radius of a dynamic obstacle (in mm)",
        envvar="PLANNER_OBSTACLE_RADIUS"
    ),
    obstacle_bb_margin: float = typer.Option(
        0.2, min=0, max=1,
        help="Obstacle bounding box margin in percent of the radius",
        envvar="PLANNER_OBSTACLE_BB_MARGIN"
    ),
    obstacle_bb_vertices: int = typer.Option(
        6, min=3, max=20,
        help="Number of obstacle bounding box vertices",
        envvar="PLANNER_OBSTACLE_BB_VERTICES"
    ),
    max_distance: int = typer.Option(
        2500, min=0, max=4000,
        help="Maximum distance to take avoidance points into account (mm)",
        envvar=["COGIP_MAX_DISTANCE", "PLANNER_MAX_DISTANCE"]
    ),
    obstacle_sender_interval: float = typer.Option(
        0.2, min=0.1, max=2.0,
        help="Interval between each send of obstacles to dashboards (in seconds)",
        envvar="PLANNER_OBSTACLE_SENDER_INTERVAL"
    ),
    path_refresh_interval: float = typer.Option(
        0.2, min=0.1, max=2.0,
        help="Interval between each update of robot paths (in seconds)",
        envvar="PLANNER_PATH_REFRESH_INTERVAL"
    ),
    launcher_speed: int = typer.Option(
        75, min=0, max=100,
        help="Launcher speed",
        envvar="PLANNER_LAUNCHER_SPEED"
    ),
    esc_speed: int = typer.Option(
        3, min=0, max=5,
        help="ESC speed",
        envvar="PLANNER_ESC_SPEED"
    ),
    plot: bool = typer.Option(
        False,
        "-p", "--plot",
        help="Display avoidance graph in realtime",
        envvar=["PLANNER_PLOT"]
    ),
    reload: bool = typer.Option(
        False,
        "-r", "--reload",
        help="Reload app on source file changes",
        envvar=["COGIP_RELOAD", "PLANNER_RELOAD"]
    ),
    debug: bool = typer.Option(
        False,
        "-d", "--debug",
        help="Turn on debug messages",
        envvar=["COGIP_DEBUG", "PLANNER_DEBUG"]
    )
):
    if debug:
        logger.setLevel(logging.DEBUG)

    # The reload option is not working since multiprocessing is used to compute avoidance.
    # It will be debugged later.
    if reload:
        reload = False
        logger.warning("-r/--reload option currently not active")

    args = (
        server_url,
        robot_width,
        obstacle_radius,
        obstacle_bb_margin,
        obstacle_bb_vertices,
        max_distance,
        obstacle_sender_interval,
        path_refresh_interval,
        launcher_speed,
        esc_speed,
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
    Launch COGIP Game Planner.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-planner` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == '__main__':
    main()

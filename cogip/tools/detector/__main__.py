#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Optional

import typer
from watchfiles import PythonFilter, run_process

from . import logger
from .detector import Detector


def changes_callback(changes):
    logger.info(f"Changes detected: {changes}")


def run(*args, **kwargs) -> None:
    detector = Detector(*args, **kwargs)
    detector.connect()


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
        envvar=["ROBOT_ID", "DETECTOR_ID"]
    ),
    lidar_port: Optional[Path] = typer.Option(
        None,
        "-p", "--lidar-port",
        help="Serial port connected to the Lidar",
        envvar="DETECTOR_LIDAR_PORT"
    ),
    min_distance: int = typer.Option(
        150, min=0, max=1000,
        help="Minimum distance to detect an obstacle (mm)",
        envvar="DETECTOR_MIN_DISTANCE"
    ),
    max_distance: int = typer.Option(
        2500, min=0, max=3000,
        help="Maximum distance to detect an obstacle (mm)",
        envvar="DETECTOR_MAX_DISTANCE"
    ),
    beacon_radius: int = typer.Option(
        35, min=10, max=150,
        help="Radius of the opponent beacon support (a cylinder of 70mm diameter to a cube of 100mm width)",
        envvar="DETECTOR_BEACON_RADIUS"
    ),
    refresh_interval: float = typer.Option(
        0.2, min=0.1, max=2.0,
        help="Interval between each update of the obstacle list (in seconds)",
        envvar="DETECTOR_REFRESH_INTERVAL"
    ),
    emulation: bool = typer.Option(
        False,
        "-e", "--emulation",
        help="Force emulation mode.",
        envvar=["DETECTOR_EMULATION"]
    ),
    reload: bool = typer.Option(
        False,
        "-r", "--reload",
        help="Reload app on source file changes.",
        envvar=["COGIP_RELOAD", "DETECTOR_RELOAD"]
    ),
    debug: bool = typer.Option(
        False,
        "-d", "--debug",
        help="Turn on debug messages.",
        envvar=["COGIP_DEBUG", "DETECTOR_DEBUG"]
    )
):
    if debug:
        logger.setLevel(logging.DEBUG)

    args = (
        server_url,
        id,
        lidar_port,
        min_distance,
        max_distance,
        beacon_radius,
        refresh_interval,
        emulation
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
    Launch COGIP Obstacle Detector.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-detector` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import logging
from pathlib import Path
from typing import Annotated, Optional

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
    server_url: Annotated[
        Optional[str],  # noqa
        typer.Option(
            help="Socket.IO Server URL",
            envvar="COGIP_SOCKETIO_SERVER_URL",
        ),
    ] = None,
    id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=1,
            help="Robot ID.",
            envvar=["ROBOT_ID", "DETECTOR_PAMI_ID"],
        ),
    ] = 1,
    tof_bus: Annotated[
        Optional[int],  # noqa
        typer.Option(
            "-tp",
            "--tof-bus",
            help="ToF i2c bus (integer, ex: 1)",
            envvar="DETECTOR_PAMI_TOF_BUS",
        ),
    ] = None,
    tof_address: Annotated[
        Optional[int],  # noqa
        typer.Option(
            "-ta",
            "--tof-address",
            parser=lambda value: int(value, 16),
            help="ToF i2c address (hex, ex: 0x29)",
            envvar="DETECTOR_PAMI_TOF_ADDRESS",
        ),
    ] = None,
    min_distance: Annotated[
        int,
        typer.Option(
            min=0,
            max=1000,
            help="Minimum distance to detect an obstacle (mm)",
            envvar="DETECTOR_PAMI_MIN_DISTANCE",
        ),
    ] = 150,
    max_distance: Annotated[
        int,
        typer.Option(
            min=0,
            max=4000,
            help="Maximum distance to detect an obstacle (mm)",
            envvar=["DETECTOR_PAMI_MAX_DISTANCE"],
        ),
    ] = 2500,
    refresh_interval: Annotated[
        float,
        typer.Option(
            min=0.1,
            max=2.0,
            help="Interval between each update of the obstacle list (in seconds)",
            envvar="DETECTOR_PAMI_REFRESH_INTERVAL",
        ),
    ] = 0.2,
    reload: Annotated[
        bool,
        typer.Option(
            "-r",
            "--reload",
            help="Reload app on source file changes.",
            envvar=["COGIP_RELOAD", "DETECTOR_PAMI_RELOAD"],
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages.",
            envvar=["COGIP_DEBUG", "DETECTOR_PAMI_DEBUG"],
        ),
    ] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)

    if not server_url:
        server_url = f"http://localhost:809{id}"

    args = (
        server_url,
        tof_bus,
        tof_address,
        min_distance,
        max_distance,
        refresh_interval,
    )

    if reload:
        watch_dir = Path(__file__).parent.parent.parent
        run_process(
            watch_dir,
            target=run,
            args=args,
            callback=changes_callback,
            watch_filter=PythonFilter(),
            debug=False,
        )
    else:
        run(*args)


def main():
    """
    Launch COGIP PAMI Obstacle Detector.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-detector-pami` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()

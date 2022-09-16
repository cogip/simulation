#!/usr/bin/env python3
import logging
from typing import Optional

import typer

from . import logger
from .detector import Detector


def main_opt(
    uart_port: Optional[str] = typer.Option(
        None,
        help="Serial port connected to the Lidar",
        envvar="DETECTOR_UART_PORT"
    ),
    uart_speed: int = typer.Option(
        230400,
        help="Baud rate",
        envvar="DETECTOR_UART_SPEED"
    ),
    copilot_url: str = typer.Option(
        "http://localhost:8080",
        help="Copilot URL",
        envvar="DETECTOR_COPILOT_URL"
    ),
    min_distance: int = typer.Option(
        150,
        help="Minimum distance to detect an obstacle",
        envvar="DETECTOR_MIN_DISTANCE"
    ),
    max_distance: int = typer.Option(
        1200,
        help="Maximum distance to detect an obstacle",
        envvar="DETECTOR_MAX_DISTANCE"
    ),
    lidar_min_intensity: int = typer.Option(
        1000,
        help="Minimum intensity required to validate a Lidar distance",
        envvar="DETECTOR_LIDAR_MIN_INTENSITY"
    ),
    obstacle_radius: int = typer.Option(
        500,
        help="Radius of a dynamic obstacle",
        envvar="DETECTOR_OBSTACLE_RADIUS"
    ),
    obstacle_bb_margin: float = typer.Option(
        0.2,
        help="Obstacle bounding box margin in percent of the radius",
        envvar="DETECTOR_OBSTACLE_BB_MARGIN"
    ),
    obstacle_bb_vertices: int = typer.Option(
        6,
        help="Number of obstacle bounding box vertices",
        envvar="DETECTOR_OBSTACLE_BB_VERTICES"
    ),
    beacon_radius: int = typer.Option(
        35,
        help="Radius of the opponent beacon support (a cylinder of 70mm diameter to a cube of 100mm width)",
        envvar="DETECTOR_OBSTACLE_RADIUS"
    ),
    refresh_interval: float = typer.Option(
        0.1,
        help="Interval between each update of the obstacle list (in seconds)",
        envvar="DETECTOR_REFRESH_INTERVAL"
    ),
    debug: bool = typer.Option(
        False,
        "-d", "--debug",
        help="Turn on debug messages.",
        envvar="DETECTOR_DEBUG",
    )
):
    if debug:
        logger.setLevel(logging.DEBUG)

    detector = Detector(
        uart_port,
        uart_speed,
        copilot_url,
        min_distance,
        max_distance,
        lidar_min_intensity,
        obstacle_radius,
        obstacle_bb_margin,
        obstacle_bb_vertices,
        beacon_radius,
        refresh_interval
    )
    detector.connect()


def main():
    """
    Launch COGIP Obstacle Detector.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-detector` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == '__main__':
    main()

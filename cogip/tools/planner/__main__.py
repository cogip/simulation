#!/usr/bin/env python3
import logging

import typer

from . import logger
from .planner import Planner


def main_opt(
    copilot_url: str = typer.Option(
        "http://localhost:8080",
        help="Copilot URL",
        envvar="PLANNER_COPILOT_URL"
    ),
    debug: bool = typer.Option(
        False,
        "-d", "--debug",
        help="Turn on debug messages.",
        envvar="PLANNER_DEBUG",
    )
):
    if debug:
        logger.setLevel(logging.DEBUG)

    planner = Planner(
        copilot_url,
    )
    planner.connect()


def main():
    """
    Launch COGIP Game Planner.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-planner` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == '__main__':
    main()

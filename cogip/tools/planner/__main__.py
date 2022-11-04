#!/usr/bin/env python3
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
    planner.connect()


def main_opt(
    server_url: str = typer.Option(
        "http://localhost:8080",
        help="Server URL",
        envvar="COGIP_SERVER_URL"
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

    args = (server_url,)

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

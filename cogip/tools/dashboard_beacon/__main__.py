#!/usr/bin/env python3
import logging
from pathlib import Path

import typer
import uvicorn
from watchfiles import PythonFilter, run_process

from . import logger


def changes_callback(changes):
    logger.info(f"Changes detected: {changes}")


def main_opt(
    reload: bool = typer.Option(
        False,
        "-r",
        "--reload",
        help="Reload app on source file changes",
        envvar=["COGIP_RELOAD", "DASHBOARD_BEACON_RELOAD"],
    ),
    debug: bool = typer.Option(
        False,
        "-d",
        "--debug",
        help="Turn on debug messages",
        envvar=["COGIP_DEBUG", "DASHBOARD_BEACON_DEBUG"],
    ),
):
    if debug:
        logger.setLevel(logging.DEBUG)

    uvicorn_args = ("cogip.tools.dashboard_beacon.app:app",)
    uvicorn_kwargs = {
        "host": "0.0.0.0",
        "port": 8080,
        "workers": 1,
        "log_level": "warning",
    }

    if reload:
        watch_dir = Path(__file__).parent.parent.parent
        run_process(
            watch_dir,
            target=uvicorn.run,
            args=uvicorn_args,
            kwargs=uvicorn_kwargs,
            callback=changes_callback,
            watch_filter=PythonFilter(),
            debug=False,
        )
    else:
        uvicorn.run(*uvicorn_args, **uvicorn_kwargs)


def main():
    """
    Launch COGIP Beacon Dashboard.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-dashboard-beacon` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()

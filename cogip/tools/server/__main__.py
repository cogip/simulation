#!/usr/bin/env python3
import logging
import os
from pathlib import Path

import typer
import uvicorn
from watchfiles import PythonFilter, run_process

from . import logger


def changes_callback(changes):
    logger.info(f"Changes detected: {changes}")


def main_opt(
    id: int = typer.Option(
        0,
        "-i", "--id",
        min=0,
        max=9,
        help="Robot ID.",
        envvar=["ROBOT_ID", "SERVER_ID"]
    ),
    record_dir: Path = typer.Option(
        Path("/var/tmp/cogip"),
        help="Directory where games will be recorded",
        envvar="SERVER_RECORD_DIR"
    ),
    reload: bool = typer.Option(
        False,
        "-r", "--reload",
        help="Reload app on source file changes",
        envvar=["COGIP_RELOAD", "SERVER_RELOAD"]
    ),
    debug: bool = typer.Option(
        False,
        "-d", "--debug",
        help="Turn on debug messages",
        envvar=["COGIP_DEBUG", "SERVER_DEBUG"]
    )
):
    if debug:
        logger.setLevel(logging.DEBUG)

    os.environ["SERVER_RECORD_DIR"] = str(record_dir)

    uvicorn_args = ("cogip.tools.server.app:app",)
    uvicorn_kwargs = {
        "host": "0.0.0.0",
        "port": 8090 + id,
        "workers": 1,
        "log_level": "warning"
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
            debug=False
        )
    else:
        uvicorn.run(*uvicorn_args, **uvicorn_kwargs)


def main():
    """
    Launch COGIP SocketIO/Web server.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-server` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == '__main__':
    main()

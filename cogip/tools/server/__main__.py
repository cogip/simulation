#!/usr/bin/env python3
import logging
import os
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from watchfiles import PythonFilter, run_process

from . import logger


def changes_callback(changes):
    logger.info(f"Changes detected: {changes}")


def main_opt(
    id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=1,
            max=9,
            help="Robot ID.",
            envvar=["ROBOT_ID", "SERVER_ID"],
        ),
    ] = 1,
    record_dir: Annotated[
        Path,
        typer.Option(
            help="Directory where games will be recorded",
            envvar="SERVER_RECORD_DIR",
        ),
    ] = Path("/var/tmp/cogip"),
    reload: Annotated[
        bool,
        typer.Option(
            "-r",
            "--reload",
            help="Reload app on source file changes",
            envvar=["COGIP_RELOAD", "SERVER_RELOAD"],
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages",
            envvar=["COGIP_DEBUG", "SERVER_DEBUG"],
        ),
    ] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)

    os.environ["SERVER_RECORD_DIR"] = str(record_dir)

    uvicorn_args = ("cogip.tools.server.app:app",)
    uvicorn_kwargs = {
        "host": "0.0.0.0",
        "port": 8090 + id,
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
    Launch COGIP SocketIO/Web server.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-server` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()

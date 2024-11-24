#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from watchfiles import PythonFilter, run_process

from . import logger
from .copilot import Copilot


def changes_callback(changes):
    logger.info(f"Changes detected: {changes}")


def run(*args, **kwargs) -> None:
    copilot = Copilot(*args, **kwargs)
    asyncio.run(copilot.run())


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
            envvar=["ROBOT_ID", "COPILOT_ID"],
        ),
    ] = 1,
    can_channel: Annotated[
        str,
        typer.Option(
            "-c",
            "--can-channel",
            help="CAN channel connected to STM32 modules",
            envvar="COPILOT_CAN_CHANNEL",
        ),
    ] = "vcan0",
    can_bitrate: Annotated[
        int,
        typer.Option(
            "-b",
            "--can-bitrate",
            help="CAN bitrate",
            envvar="COPILOT_CAN_BITRATE",
        ),
    ] = 500000,
    can_data_bitrate: Annotated[
        int,
        typer.Option(
            "-B",
            "--data-bitrate",
            help="CAN FD data bitrate",
            envvar="COPILOT_CANFD_DATA_BITRATE",
        ),
    ] = 1000000,
    reload: Annotated[
        bool,
        typer.Option(
            "-r",
            "--reload",
            help="Reload app on source file changes",
            envvar=["COGIP_RELOAD", "COPILOT_RELOAD"],
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "-d",
            "--debug",
            help="Turn on debug messages",
            envvar=["COGIP_DEBUG", "COPILOT_DEBUG"],
        ),
    ] = False,
):
    if debug:
        logger.setLevel(logging.DEBUG)

    if not server_url:
        server_url = f"http://localhost:809{id}"

    args = (server_url, id, can_channel, can_data_bitrate, can_bitrate)
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
    Launch COGIP Copilot.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-copilot` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()

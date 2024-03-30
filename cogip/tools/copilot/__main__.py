#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path
from typing import Optional

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
    server_url: Optional[str] = typer.Option(  # noqa
        None,
        help="Socket.IO Server URL",
        envvar="COGIP_SOCKETIO_SERVER_URL",
    ),
    id: int = typer.Option(
        1,
        "-i",
        "--id",
        min=1,
        help="Robot ID.",
        envvar=["ROBOT_ID", "COPILOT_ID"],
    ),
    can_channel: str = typer.Option(
        "vcan0",
        "-c",
        "--can-channel",
        help="CAN channel connected to STM32 modules",
        envvar="COPILOT_CAN_CHANNEL",
    ),
    can_bitrate: int = typer.Option(
        500000,
        "-b",
        "--can-bitrate",
        help="CAN bitrate",
        envvar="COPILOT_CAN_BITRATE",
    ),
    can_data_bitrate: int = typer.Option(
        1000000,
        "-B",
        "--data-bitrate",
        help="CAN FD data bitrate",
        envvar="COPILOT_CANFD_DATA_BITRATE",
    ),
    reload: bool = typer.Option(
        False,
        "-r",
        "--reload",
        help="Reload app on source file changes",
        envvar=["COGIP_RELOAD", "COPILOT_RELOAD"],
    ),
    debug: bool = typer.Option(
        False,
        "-d",
        "--debug",
        help="Turn on debug messages",
        envvar=["COGIP_DEBUG", "COPILOT_DEBUG"],
    ),
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

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-copilot` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()

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
        envvar=["ROBOT_ID", "COPILOT_PAMI_ID"],
    ),
    serial_port: Path = typer.Option(
        "/dev/ttyUSB0",
        "-p",
        "--serial-port",
        help="Serial port connected to STM32 device",
        envvar="COPILOT_PAMI_SERIAL_PORT",
    ),
    serial_baud: int = typer.Option(
        230400,
        "-b",
        "--serial-baudrate",
        help="Baud rate",
        envvar="COPILOT_PAMI_BAUD_RATE",
    ),
    reload: bool = typer.Option(
        False,
        "-r",
        "--reload",
        help="Reload app on source file changes",
        envvar=["COGIP_RELOAD", "COPILOT_PAMI_RELOAD"],
    ),
    debug: bool = typer.Option(
        False,
        "-d",
        "--debug",
        help="Turn on debug messages",
        envvar=["COGIP_DEBUG", "COPILOT_PAMI_DEBUG"],
    ),
):
    if debug:
        logger.setLevel(logging.DEBUG)

    if not server_url:
        server_url = f"http://localhost:809{id}"

    args = (server_url, id, serial_port, serial_baud)
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
    Launch COGIP PAMI Copilot.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-copilot-pami` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()

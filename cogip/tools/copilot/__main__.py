#!/usr/bin/env python3
from pathlib import Path

import typer
import uvicorn

from .copilot import Copilot


def main_opt(
        serial_port: Path = typer.Option(
            "/dev/ttyUSB0",
            "--serial", "-s",
            exists=True, file_okay=True,
            help="Serial port connected to STM32 device"),
        serial_baud: int = typer.Option(
            230400,
            "--baud", "-b",
            help="Baud rate"),
        server_port: int = typer.Option(
            80,
            "--port", "-p",
            help="Socket.IO/Web server port")) -> None:
    """
    Launch COGIP Copilot.
    """
    copilot = Copilot()
    copilot.port = serial_port
    copilot.baud = serial_baud

    uvicorn.run(
        "cogip.tools.copilot.app:app",
        host="0.0.0.0",
        port=server_port,
        log_level="warning"
    )


def main():
    """
    Starts the copilot.

    During installation of the simulation tools, `setuptools` is configured
    to create the `copilot` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == '__main__':
    main()

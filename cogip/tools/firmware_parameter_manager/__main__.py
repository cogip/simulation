import asyncio
from typing import Annotated

import socketio
import typer

from cogip.tools.firmware_parameter_manager import shell
from cogip.tools.firmware_parameter_manager.firmware_parameter_manager import FirmwareParameterManager
from cogip.utils.console_ui import ConsoleUI


async def main_async(server_url: str) -> None:
    sio = socketio.AsyncClient(logger=False)
    manager = FirmwareParameterManager(sio)

    await sio.connect(server_url, namespaces=[manager.namespace])
    try:
        await shell.run(manager, ConsoleUI())
    finally:
        await sio.disconnect()


def main_opt(
    *,
    server_url: Annotated[
        str | None,
        typer.Option(
            help="Socket.IO Server URL",
            envvar="COGIP_SOCKETIO_SERVER_URL",
        ),
    ] = None,
    robot_id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=1,
            help="Robot ID.",
            envvar=["ROBOT_ID"],
        ),
    ] = 1,
):
    if not server_url:
        server_url = f"http://localhost:809{robot_id}"

    asyncio.run(main_async(server_url))


def main():
    """
    Run firmware parameter manager utility.

    During installation of cogip-tools, `setuptools` is configured
    to create the `cogip-firmware-parameter-manager` script using this function as entrypoint.
    """
    typer.run(main_opt)


if __name__ == "__main__":
    main()

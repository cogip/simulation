#!/usr/bin/env python3
import uvicorn

from .settings import Settings


def main() -> None:
    """
    Launch COGIP Robot Camera.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-robotcam` script using this function as entrypoint.
    """
    settings = Settings()

    uvicorn.run(
        "cogip.tools.robotcam.app:app",
        host="0.0.0.0",
        port=settings.server_port,
        workers=settings.nb_workers,
        log_level="warning"
    )

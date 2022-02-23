#!/usr/bin/env python3
import uvicorn

from .settings import Settings


def main() -> None:
    """
    Launch COGIP Copilot.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-copilot` script using this function as entrypoint.
    """
    settings = Settings()

    uvicorn.run(
        "cogip.tools.copilot.app:app",
        host="0.0.0.0",
        port=settings.server_port,
        workers=1,
        log_level="warning"
    )

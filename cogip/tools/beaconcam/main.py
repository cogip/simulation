#!/usr/bin/env python3
from multiprocessing import Process

import uvicorn

from .camera import CameraHandler
from .settings import Settings


def start_camera_handler():
    camera = CameraHandler()
    camera.camera_handler()


def main() -> None:
    """
    Launch COGIP Beacon Camera.

    During installation of the simulation tools, `setuptools` is configured
    to create the `cogip-beaconcam` script using this function as entrypoint.
    """
    settings = Settings()

    # Start Camera handler process
    p = Process(target=start_camera_handler)
    p.start()

    # Start web server
    uvicorn.run(
        "cogip.tools.beaconcam.app:app",
        host="0.0.0.0",
        port=8090,
        workers=settings.nb_workers,
        log_level="warning"
    )

    p.terminate()

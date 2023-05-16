from fastapi import FastAPI

from .server import CameraServer


def create_app() -> FastAPI:
    """
    Create server and return FastAPI application for uvicorn/gunicorn.
    """
    server = CameraServer()
    return server.app


app = create_app()

from fastapi import FastAPI

from .server import Server


def create_app() -> FastAPI:
    """
    Create server and return FastAPI application for uvicorn/gunicorn.
    """
    server = Server()
    return server.app


app = create_app()

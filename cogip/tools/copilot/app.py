from fastapi import FastAPI

from .server import CopilotServer


def create_app() -> FastAPI:
    """
    Create server and return FastAPI application for uvicorn/gunicorn.
    """
    server = CopilotServer()
    return server.app


app = create_app()

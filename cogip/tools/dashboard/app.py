from fastapi import FastAPI

from .dashboard import Dashboard


def create_app() -> FastAPI:
    """
    Create server and return FastAPI application for uvicorn/gunicorn.
    """
    dashboard = Dashboard()
    return dashboard.app


app = create_app()

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn.main import Server

from . import routes


class Dashboard:
    _exiting: bool = False  # True if Uvicorn server was ask to shutdown
    _original_uvicorn_exit_handler = Server.handle_exit  # Backup of original exit handler to overload it

    def __init__(self):
        """
        Class constructor.

        Create FastAPI application.
        """
        self.app = FastAPI(title="COGIP Web Monitor", debug=False)

        # Overload default Uvicorn exit handler
        Server.handle_exit = self.handle_exit

        # Mount static files
        current_dir = Path(__file__).parent
        self.app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

        # Create HTML templates
        self.templates = Jinja2Templates(directory=current_dir / "templates")

        # Register routes
        self.app.include_router(routes.BeaconRouter(self.templates), prefix="")

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        Dashboard._exiting = True
        Dashboard._original_uvicorn_exit_handler(*args, **kwargs)

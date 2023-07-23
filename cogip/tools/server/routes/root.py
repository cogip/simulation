import socketio

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


class RootRouter(APIRouter):

    def __init__(self, templates: Jinja2Templates, sio: socketio.AsyncServer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sio = sio

        @self.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """
            Homepage of the dashboard web server.
            """
            return templates.TemplateResponse("index.html", {"request": request})

        @self.put("/cherries", response_class=HTMLResponse)
        async def cherries(count: int, request: Request):
            await self.sio.emit("cherries", count, namespace="/planner")

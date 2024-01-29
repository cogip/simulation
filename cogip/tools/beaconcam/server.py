from datetime import datetime
from multiprocessing.shared_memory import SharedMemory
from pathlib import Path
from threading import Thread

import cv2
import numpy as np
import polling2
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from uvicorn.main import Server as UvicornServer

from cogip import logger
from cogip.tools.planner.camp import Camp
from .settings import Settings


class CameraServer:
    """
    Camera web server.

    Handle FastAPI server to stream camera video and SocketIO client.
    """
    _exiting: bool = False                              # True if Uvicorn server was ask to shutdown
    _last_frame: SharedMemory = None                    # Last generated frame to stream on web server
    _original_uvicorn_exit_handler = UvicornServer.handle_exit

    def __init__(self):
        """
        Class constructor.

        Create FastAPI application and SocketIO client.
        """
        self.settings = Settings()
        CameraServer._exiting = False

        self.app = FastAPI(title="COGIP Beacon Camera Streamer", debug=False)
        self.register_endpoints()

        UvicornServer.handle_exit = self.handle_exit

        self.records_dir = Path.home() / "records"
        self.records_dir.mkdir(exist_ok=True)
        # Keep only 100 last records
        for old_record in sorted(self.records_dir.glob('*.jpg'))[:-100]:
            old_record.unlink()

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        CameraServer._exiting = True

        if CameraServer._last_frame:
            try:
                CameraServer._last_frame.close()
                logger.info("Camera server: Detached shared memory for last frame.")
            except FileNotFoundError:
                pass

        CameraServer._original_uvicorn_exit_handler(*args, **kwargs)

    def camera_connect(self) -> bool:
        if self._exiting:
            return True

        try:
            CameraServer._last_frame = SharedMemory(name="last_frame")
        except Exception:
            CameraServer._last_frame = None
            logger.warning("Camera server: Failed to attach to shared memory last_frame, retrying in 1s.")
            return False
        logger.info("Camera server: Attached to shared memory last_frame.")
        return True

    async def camera_streamer(self):
        """
        Frame generator.
        Yield frames produced by [camera_handler][cogip.tools.beaconcam.camera.CameraHandler.camera_handler].
        """
        while not self._exiting:
            yield b'--frame\r\n'
            yield b'Content-Type: image/bmp\r\n\r\n'
            yield bytes(self._last_frame.buf)
            yield b'\r\n'

    def register_endpoints(self) -> None:

        @self.app.on_event("startup")
        async def startup_event():
            """
            Function called at FastAPI server startup.
            """
            # Poll in background to wait for camera server connection through shared memory.
            Thread(target=lambda: polling2.poll(
                self.camera_connect,
                step=1,
                poll_forever=True
            )).start()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """
            Function called at FastAPI server shutdown.
            """
            pass

        @self.app.get("/")
        def index():
            """
            Camera stream.
            """
            stream = self.camera_streamer() if CameraServer._last_frame else ""
            return StreamingResponse(stream, media_type="multipart/x-mixed-replace;boundary=frame")

        @self.app.get("/snapshot", status_code=200)
        async def snapshot(camp: Camp.Colors):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = f"beacon-snapshot-{timestamp}-{camp.name}"

            jpg_as_np = np.frombuffer(self._last_frame.buf, dtype=np.uint8)
            frame = cv2.imdecode(jpg_as_np, flags=1)
            record_filename_full = self.records_dir / f"{basename}_full.jpg"
            cv2.imwrite(str(record_filename_full), frame)

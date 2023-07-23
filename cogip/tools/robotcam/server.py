from datetime import datetime
from multiprocessing.shared_memory import SharedMemory
from pathlib import Path
from threading import Thread

import cv2
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import numpy as np
import polling2
from uvicorn.main import Server as UvicornServer

from cogip import logger
from .settings import Settings


class CameraServer():
    """
    Camera web server.

    Handle FastAPI server to stream camera video and SocketIO client to send detected samples to server.
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

        self.app = FastAPI(title="COGIP Robot Camera Streamer", debug=False)
        self.register_endpoints()

        UvicornServer.handle_exit = self.handle_exit

        self.records_dir = Path.home() / "records"
        self.records_dir.mkdir(exist_ok=True)
        # Keep only 100 last records
        for old_record in sorted(self.records_dir.glob('*.jpg'))[:-100]:
            old_record.unlink()

        self.crop_zones = {
            1: (295, 480, 170, 540),
            2: (295, 480, 170, 540)
        }

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
        Yield frames produced by [camera_handler][cogip.tools.robotcam.camera.CameraHandler.camera_handler].
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

        @self.app.get("/cherry_on_cake", status_code=200)
        async def cherry_on_cake() -> bool:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = f"robot{self.settings.id}-{timestamp}"
            start_row, end_row, start_col, end_col = self.crop_zones[self.settings.id]

            jpg_as_np = np.frombuffer(self._last_frame.buf, dtype=np.uint8)
            frame = cv2.imdecode(jpg_as_np, flags=1)
            record_filename_full = self.records_dir / f"{basename}_full.jpg"
            cv2.imwrite(str(record_filename_full), frame)

            frame_crop = frame[start_row:end_row, start_col:end_col]
            record_filename_crop = self.records_dir / f"{basename}_crop.jpg"
            cv2.imwrite(str(record_filename_crop), frame_crop)

            frame_hsv = cv2.cvtColor(frame_crop, cv2.COLOR_BGR2HSV)

            red_low = np.array([128, 148, 0])
            red_high = np.array([189, 225, 241])
            mask = cv2.inRange(frame_hsv, red_low, red_high)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            record_filename_mask = self.records_dir / f"{basename}_mask.jpg"
            cv2.imwrite(str(record_filename_mask), mask)

            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # TODO: filter on circle size

            # Use a list to store the center and radius of the target circles:
            detectedCircles = []

            # Look for the outer contours:
            for i, c in enumerate(contours):
                # Approximate the contour to a circle:
                (x, y), radius = cv2.minEnclosingCircle(c)

                # Compute the center and radius:
                center = (int(x), int(y))
                radius = int(radius)

                # Draw the circles:
                cv2.circle(frame, center, radius, (0, 255, 0), 2)

                # Store the center and radius:
                detectedCircles.append([center, radius])

            suffix = "ok" if len(contours) > 0 else "ko"
            record_filename_circle = self.records_dir / f"{basename}_circle_{suffix}.jpg"
            cv2.imwrite(str(record_filename_circle), frame)

            return (len(contours) > 0)

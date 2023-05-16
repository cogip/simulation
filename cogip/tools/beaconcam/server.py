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
from cogip.models.artifacts import CakeSlotID, CakeLayerKind
from cogip.tools.planner.camp import Camp
from .settings import Settings


class CameraServer():
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

        self.camp_column_shifts: dict[Camp.Colors, int] = {
            Camp.Colors.blue: 0,  # -
            Camp.Colors.green: 0,  # +

        }
        self.crop_zones: dict[CakeSlotID, tuple[CakeLayerKind, int, int, int, int]] = {
            CakeSlotID.GREEN_FRONT_SPONGE: (CakeLayerKind.SPONGE, 295, 480, 265, 470),
            CakeSlotID.GREEN_FRONT_CREAM: (CakeLayerKind.CREAM, 295, 480, 265, 470),
            CakeSlotID.GREEN_FRONT_ICING: (CakeLayerKind.ICING, 93, 121, 371, 401),
            CakeSlotID.GREEN_BACK_SPONGE: (CakeLayerKind.SPONGE, 295, 480, 265, 470),
            CakeSlotID.GREEN_BACK_CREAM: (CakeLayerKind.CREAM, 295, 480, 265, 470),
            CakeSlotID.GREEN_BACK_ICING: (CakeLayerKind.ICING, 295, 480, 265, 470),
            CakeSlotID.BLUE_FRONT_SPONGE: (CakeLayerKind.SPONGE, 295, 480, 265, 470),
            CakeSlotID.BLUE_FRONT_CREAM: (CakeLayerKind.CREAM, 295, 480, 265, 470),
            CakeSlotID.BLUE_FRONT_ICING: (CakeLayerKind.ICING, 295, 480, 265, 470),
            CakeSlotID.BLUE_BACK_SPONGE: (CakeLayerKind.SPONGE, 295, 480, 265, 470),
            CakeSlotID.BLUE_BACK_CREAM: (CakeLayerKind.CREAM, 295, 480, 265, 470),
            CakeSlotID.BLUE_BACK_ICING: (CakeLayerKind.ICING, 295, 480, 265, 470),
        }
        self.colors: dict[CakeLayerKind, tuple[np.ndarray, np.ndarray]] = {
            CakeLayerKind.SPONGE: (np.array([0, 34, 18]), np.array([20, 237, 73])),
            CakeLayerKind.CREAM: (np.array([18, 97, 119]), np.array([60, 195, 255])),
            CakeLayerKind.ICING: (np.array([130, 63, 124]), np.array([176, 255, 255]))
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

        @self.app.get("/check", status_code=200)
        async def check(camp: Camp.Colors, slot: CakeSlotID) -> bool:
            col_shift = self.camp_column_shifts[camp]
            kind, start_row, end_row, start_col, end_col = self.crop_zones[slot]
            start_col += col_shift
            end_col += col_shift
            color_low, color_high = self.colors[kind]

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = f"beacon-{timestamp}-{camp.name}-{slot.name}-{kind.name}"

            jpg_as_np = np.frombuffer(self._last_frame.buf, dtype=np.uint8)
            frame = cv2.imdecode(jpg_as_np, flags=1)
            record_filename_full = self.records_dir / f"{basename}_full.jpg"
            cv2.imwrite(str(record_filename_full), frame)

            frame_crop = frame[start_row:end_row, start_col:end_col]
            record_filename_crop = self.records_dir / f"{basename}_crop.jpg"
            cv2.imwrite(str(record_filename_crop), frame_crop)

            frame_hsv = cv2.cvtColor(frame_crop, cv2.COLOR_BGR2HSV)

            mask = cv2.inRange(frame_hsv, color_low, color_high)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            color_ratio = cv2.countNonZero(mask) / (frame_crop.size / 3)
            record_filename_mask = self.records_dir / f"{basename}_mask_{int(color_ratio * 100)}.jpg"
            cv2.imwrite(str(record_filename_mask), mask)

            return (color_ratio > 0.5)

        @self.app.get("/snapshot", status_code=200)
        async def snapshot(camp: Camp.Colors):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = f"beacon-snapshot-{timestamp}-{camp.name}"

            jpg_as_np = np.frombuffer(self._last_frame.buf, dtype=np.uint8)
            frame = cv2.imdecode(jpg_as_np, flags=1)
            record_filename_full = self.records_dir / f"{basename}_full.jpg"
            cv2.imwrite(str(record_filename_full), frame)

            col_shift = self.camp_column_shifts[camp]

            for slot, crop_zone in self.crop_zones.items():
                kind, start_row, end_row, start_col, end_col = crop_zone
                start_col += col_shift
                end_col += col_shift
                color_low, color_high = self.colors[kind]
                slot_basename = f"{basename}-{slot.name}-{kind.name}"

                frame_crop = frame[start_row:end_row, start_col:end_col]
                record_filename_crop = self.records_dir / f"{slot_basename}_crop.jpg"
                cv2.imwrite(str(record_filename_crop), frame_crop)

                frame_hsv = cv2.cvtColor(frame_crop, cv2.COLOR_BGR2HSV)

                mask = cv2.inRange(frame_hsv, color_low, color_high)

                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                color_ratio = cv2.countNonZero(mask) / (frame_crop.size / 3)
                record_filename_mask = self.records_dir / f"{slot_basename}_mask_{int(color_ratio * 100)}.jpg"
                cv2.imwrite(str(record_filename_mask), mask)

import asyncio
import json
import math
from multiprocessing.shared_memory import SharedMemory
from pathlib import Path
from threading import Thread

import cv2
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import numpy as np
import polling2
import socketio
from uvicorn.main import Server as UvicornServer

from cogip import logger
from .codecs import VideoCodec
from .settings import Settings


class CameraServer():
    """
    Camera server.

    Handle camera initialization, sample detection, FastAPI server to stream camera video
    and SocketIO client to send detected samples to Copilot.
    """
    _camera_device: Path = None                         # Camera device
    _camera_codec: VideoCodec = None                    # Video codec
    _camera_frame_width: int = None                     # Camera frame width
    _camera_frame_height: int = None                    # Camera frame height
    _camera_params_file: Path = None                    # Camera intrinsics parameters
    _camera_capture: cv2.VideoCapture = None            # OpenCV video capture
    _camera_matrix_coefficients: np.ndarray = None      # Matrix coefficients from camera calibration
    _camera_distortion_coefficients: np.ndarray = None  # Distortion coefficients from camera calibration
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
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.init_camera()
        self.register_endpoints()

        # Last frame is stored in shared memory to be shared between gunicorn/uvicorn processes.
        # In case of multiple workers, the first process will create the shared memory,
        # other processes just need to attached to the existing shared memory.
        try:
            CameraServer._last_frame = SharedMemory(name="last_frame", create=True, size=self.settings.frame_size)
        except FileExistsError:
            CameraServer._last_frame = SharedMemory(name="last_frame")

        UvicornServer.handle_exit = self.handle_exit

    @staticmethod
    def handle_exit(*args, **kwargs):
        """Overload function for Uvicorn handle_exit"""
        CameraServer._exiting = True

        try:
            CameraServer._last_frame.close()
            CameraServer._last_frame.unlink()
        except FileNotFoundError:
            pass

        CameraServer._original_uvicorn_exit_handler(*args, **kwargs)

    def init_camera(self):
        """
        Initialize camera and aruco markers detection parameters.
        """
        # List all detection parameters with their default values to help further optimization
        self._camera_capture = cv2.VideoCapture(str(self.settings.camera_device), cv2.CAP_V4L2)
        if not self._camera_capture.isOpened():
            logger.error(f"Cannot open camera device {self.settings.camera_device}")
            self._camera_capture.release()
            self._camera_capture = None
            return

        fourcc = cv2.VideoWriter_fourcc(*self.settings.camera_codec.value)
        ret = self._camera_capture.set(cv2.CAP_PROP_FOURCC, fourcc)
        if not ret:
            logger.warning(f"Video codec {self.settings.camera_codec} not supported")
            self.settings.camera_codec = None

        ret = self._camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width)
        if not ret:
            logger.warning(f"Frame width {self.settings.camera_width} not supported")
            self.settings.camera_width = None

        ret = self._camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)
        if not ret:
            logger.warning(f"Frame height {self.settings.camera_height} not supported")
            self.settings.camera_height = None

        try:
            if not self.settings.camera_params.exists():
                raise OSError(f"Camera parameters file not found: {self.settings.camera_params}")
            if not self.settings.camera_params.is_file():
                raise OSError(f"Camera parameters file is not a file: {self.settings.camera_params}")
        except OSError as exc:
            logger.warning(exc)
            self.settings.camera_params = None
            self._camera_matrix_coefficients = None
            self._camera_distortion_coefficients = None
            return

        data = json.loads(self.settings.camera_params.read_text())
        self._camera_matrix_coefficients = np.array(data['mtx'])
        self._camera_distortion_coefficients = np.array(data['dist'])

    def sio_connect(self) -> bool:
        """
        Connect to Copilot's SocketIO server if application is not exiting.
        Returning True stops polling for connection to succeed.
        """
        if self._exiting:
            return True

        self.sio.connect(self.settings.copilot_url, socketio_path="sio/socket.io")
        return True

    async def camera_handler(self) -> None:
        """
        Read and process frames from camera.
        """
        loop = asyncio.get_event_loop()
        while not self._exiting:
            if self._camera_capture:
                try:
                    await loop.run_in_executor(None, self.process_image)
                except Exception as exc:
                    logger.warning(exc)
            else:
                await asyncio.sleep(1)

    def process_image(self):
        """
        Read one frame from camera, process it, send samples to Copilot
        and generate image to stream.
        """
        ret, image_color = self._camera_capture.read()
        if not ret:
            raise Exception("Can't read frame.")

        image_stream = image_color
        # Encode the frame in BMP format (larger but faster than JPEG)
        ret, encoded_image = cv2.imencode(".bmp", image_stream)
        if not ret:
            raise Exception("Can't encode frame.")

        frame = (b'--frame\r\n' b'Content-Type: image/bmp\r\n\r\n' + encoded_image.tobytes() + b'\r\n')
        self._last_frame.buf[0:len(frame)] = frame

        return encoded_image

    async def camera_streamer(self):
        """
        Frame generator.
        Yield frames produced by [camera_handler][cogip.tools.robotcam.server.CameraServer.camera_handler].
        """
        while not self._exiting:
            yield bytes(self._last_frame.buf)

    def register_endpoints(self) -> None:

        @self.app.on_event("startup")
        async def startup_event():
            """
            Function called at FastAPI server startup.
            Connect to Copilot's SocketIO server.
            Start Camera handler.
            """
            # Poll in background to wait for the first connection.
            # Deconnections/reconnections are handle directly by the client.
            Thread(target=lambda: polling2.poll(
                self.sio_connect,
                step=1,
                ignore_exceptions=(socketio.exceptions.ConnectionError),
                poll_forever=True
            )).start()

            # The camera can be used by only one worker process,
            # so start the camera handler async worker only on the process
            # that has acquired the camera.
            if self._camera_capture:
                asyncio.create_task(self.camera_handler(), name="Camera handler")

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """
            Function called at FastAPI server shutdown.
            Disconnect from Copilot's SocketIO server.
            """
            if self.sio.connected:
                self.sio.disconnect()

        @self.app.get("/")
        def index():
            """
            Camera stream.
            """
            return StreamingResponse(self.camera_streamer(), media_type="multipart/x-mixed-replace;boundary=frame")

        @self.sio.event
        def connect():
            """
            Callback on Copilot connection.
            """
            logger.info("Connected to Copilot")

        @self.sio.event
        def connect_error(data):
            """
            Callback on Copilot connection error.
            """
            logger.info("Connection to Copilot failed.")

        @self.sio.event
        def disconnect():
            """
            Callback on Copilot disconnection.
            """
            logger.info("Disconnected from Copilot")

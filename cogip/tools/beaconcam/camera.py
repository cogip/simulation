import signal
import time
from datetime import datetime

# import functools
from multiprocessing.shared_memory import SharedMemory
from pathlib import Path
from threading import Thread
from time import sleep

import cv2
import numpy as np
import polling2
import socketio

from cogip import logger
from .codecs import VideoCodec
from .settings import Settings


class ExitSignal(Exception):
    pass


class CameraHandler():
    """
    Camera handler.

    Handle camera initialization, sample detection.
    """
    _camera_device: Path = None                         # Camera device
    _camera_codec: VideoCodec = None                    # Video codec
    _camera_frame_width: int = None                     # Camera frame width
    _camera_frame_height: int = None                    # Camera frame height
    _camera_capture: cv2.VideoCapture = None            # OpenCV video capture
    _last_frame: SharedMemory = None                    # Last generated frame to stream on web server
    _frame_rate: float = 6                             # Number of images processed by seconds
    _exiting: bool = False                              # Exit requested if True

    def __init__(self):
        """
        Class constructor.

        Create SocketIO client and connect to server.
        """
        self.settings = Settings()
        signal.signal(signal.SIGTERM, self.exit_handler)

        self.record_filename: Path | None = None
        self.record_writer: cv2.VideoWriter | None = None

        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.register_sio_events()
        Thread(target=lambda: polling2.poll(
            self.sio_connect,
            step=1,
            ignore_exceptions=(socketio.exceptions.ConnectionError),
            poll_forever=True
        )).start()

    @staticmethod
    def exit_handler(signum, frame):
        """
        Function called when TERM signal is received.
        """
        CameraHandler._exiting = True
        raise ExitSignal()

    def sio_connect(self) -> bool:
        """
        Connect to SocketIO server.
        Returning True stops polling for connection to succeed.
        """
        if self._exiting:
            return True

        self.sio.connect(
            str(self.settings.socketio_server_url),
            namespaces=["/beaconcam"]
        )
        return True

    def open_camera(self):
        """
        Initialize camera and aruco markers detection parameters.
        """
        self._camera_capture = cv2.VideoCapture(str(self.settings.camera_device), cv2.CAP_V4L2)
        if not self._camera_capture.isOpened():
            logger.error(f"Camera handler: Cannot open camera device {self.settings.camera_device}")
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

    def close_camera(self) -> None:
        """
        Release camera device.
        """
        if self._camera_capture:
            try:
                self._camera_capture.release()
                logger.info("Camera handler: Camera closed.")
            except Exception as exc:  # noqa
                logger.info("Camera handler: Failed to release camera: {exc}")

        self._camera_capture = None

    def open_last_frame(self, size: int) -> None:
        """
        Open the shared memory used to exchange last frame with the server.

        Arguments:
            size: Size of the shared memory
        """
        if not self._last_frame:
            try:
                self._last_frame = SharedMemory(name="last_frame", create=True, size=size)
                logger.info("Camera handler: shared memory for last_frame created.")
            except FileExistsError as exc:
                logger.warning(f"Camera handler: Failed to create shared memory for last_frame: {exc}")
                self._last_frame = None

    def close_last_frame(self) -> None:
        """
        Close last frame shared memory.
        """
        if self._last_frame:
            try:
                self._last_frame.close()
                self._last_frame.unlink()
                logger.info("Camera handler: Shared memory for last frame closed.")
            except Exception as exc:
                logger.info(f"Camera handler: Failed to close shared memory for last frame: {exc}")

        self._last_frame = None

    def camera_handler(self) -> None:
        """
        Read and process frames from camera.
        """
        interval = 1.0 / self._frame_rate

        try:
            while not self._exiting:
                start = time.time()

                if not self._camera_capture:
                    self.open_camera()

                if not self._camera_capture:
                    logger.warning("Camera handler: Failed to open camera, retry in 1s.")
                    sleep(1)
                    continue

                try:
                    self.process_image()
                except ExitSignal:
                    break
                except Exception as exc:
                    logger.warning(f"Unknown exception: {exc}")
                    self.close_camera()
                    sleep(1)
                    continue

                now = time.time()
                duration = now - start
                if duration > interval:
                    logger.warning(f"Function too long: {duration} > {interval}")
                else:
                    wait = interval - duration
                    time.sleep(wait)

        except (KeyboardInterrupt, ExitSignal):
            pass

        logger.info("Camera handler: Exiting.")

        self.close_last_frame()
        self.close_camera()
        if self.sio.connected:
            self.sio.disconnect()

    def process_image(self) -> None:
        """
        Read one frame from camera, process it, send samples to cogip-server
        and generate image to stream.
        """
        image_color: np.ndarray
        ret, image_color = self._camera_capture.read()
        if not ret:
            raise Exception("Camera handler: Cannot read frame.")

        image_stream: np.ndarray = image_color

        # Encode the frame in BMP format (larger but faster than JPEG)
        encoded_image: np.ndarray
        ret, encoded_image = cv2.imencode(".bmp", image_stream)

        if not ret:
            raise Exception("Can't encode frame.")

        frame = encoded_image.tobytes()
        self.open_last_frame(len(frame))

        if self._last_frame:
            self._last_frame.buf[0:len(frame)] = frame

        if self.record_writer:
            self.record_writer.write(image_stream)

    def start_video_record(self):
        if self.record_writer:
            self.stop_video_record()
        records_dir = Path.home() / "records"
        records_dir.mkdir(exist_ok=True)
        # Keep only 20 last records
        for old_record in sorted(records_dir.glob('*.mp4'))[:-20]:
            old_record.unlink()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.record_filename = records_dir / f"beacon_{timestamp}.mp4"

        logger.info(f"Start recording video in {self.record_filename}")
        self.record_writer = cv2.VideoWriter(
            str(self.record_filename),
            cv2.VideoWriter_fourcc(*'mp4v'),
            self._frame_rate,
            (self.settings.camera_width, self.settings.camera_height))

    def stop_video_record(self):
        if self.record_writer:
            logger.info("Stop recording video")
            self.record_writer.release()
            self.record_filename = None
            self.record_writer = None

    def register_sio_events(self) -> None:
        @self.sio.event(namespace="/beaconcam")
        def connect():
            """
            Callback on server connection.
            """
            polling2.poll(lambda: self.sio.connected is True, step=0.2, poll_forever=True)
            logger.info("Camera handler: connected to server")
            self.sio.emit("connected", namespace="/beaconcam")

        @self.sio.event(namespace="/beaconcam")
        def connect_error(data):
            """
            Callback on server connection error.
            """
            logger.info("Camera handler: connection to server failed.")

        @self.sio.event(namespace="/beaconcam")
        def disconnect():
            """
            Callback on server disconnection.
            """
            logger.info("Camera handler: disconnected from server")

        @self.sio.on("start_video_record", namespace="/beaconcam")
        def start_video_record():
            self.start_video_record()

        @self.sio.on("stop_video_record", namespace="/beaconcam")
        def stop_video_record():
            self.stop_video_record()

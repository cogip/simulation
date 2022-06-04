from multiprocessing.shared_memory import SharedMemory
from threading import Thread

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import polling2
import socketio
from uvicorn.main import Server as UvicornServer

from cogip import logger
from .settings import Settings


class CameraServer():
    """
    Camera web server.

    Handle FastAPI server to stream camera video and SocketIO client to send detected samples to Copilot.
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
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.register_endpoints()

        UvicornServer.handle_exit = self.handle_exit

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

    def sio_connect(self) -> bool:
        """
        Connect to Copilot's SocketIO server if application is not exiting.
        Returning True stops polling for connection to succeed.
        """
        if self._exiting:
            return True

        self.sio.connect(self.settings.copilot_url, socketio_path="sio/socket.io")
        return True

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
            """
            # Poll in background to wait for the first copilot connection.
            # Deconnections/reconnections are handle directly by the client.
            Thread(target=lambda: polling2.poll(
                self.sio_connect,
                step=1,
                ignore_exceptions=(socketio.exceptions.ConnectionError),
                poll_forever=True
            )).start()

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
            Disconnect from Copilot's SocketIO server.
            """
            self.sio.reconnection = False
            self.sio.reconnection_attempts = -1
            if self.sio.connected:
                self.sio.disconnect()

        @self.app.get("/")
        def index():
            """
            Camera stream.
            """
            stream = self.camera_streamer() if CameraServer._last_frame else ""
            return StreamingResponse(stream, media_type="multipart/x-mixed-replace;boundary=frame")

        @self.sio.event
        def connect():
            """
            Callback on Copilot connection.
            """
            logger.info("Camera server connected to Copilot")

        @self.sio.event
        def connect_error(data):
            """
            Callback on Copilot connection error.
            """
            logger.info("Camera server connection to Copilot failed.")

        @self.sio.event
        def disconnect():
            """
            Callback on Copilot disconnection.
            """
            logger.info("Camera server disconnected from Copilot")

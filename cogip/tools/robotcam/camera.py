import functools
import json
import math
from multiprocessing.shared_memory import SharedMemory
from pathlib import Path
import signal
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
    _camera_params_file: Path = None                    # Camera intrinsics parameters
    _camera_capture: cv2.VideoCapture = None            # OpenCV video capture
    _camera_matrix_coefficients: np.ndarray = None      # Matrix coefficients from camera calibration
    _camera_distortion_coefficients: np.ndarray = None  # Distortion coefficients from camera calibration
    _marker_dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)  # Aruco tags dictionary
    _detector_params = cv2.aruco.DetectorParameters_create()  # Default parameters for aruco tag detection
    _last_frame: SharedMemory = None                    # Last generated frame to stream on web server
    _exiting: bool = False                              # Exit requested if True

    def __init__(self):
        """
        Class constructor.

        Create SocketIO client and connect to Copilot.
        """
        self.settings = Settings()
        signal.signal(signal.SIGTERM, self.exit_handler)

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
        Connect to Copilot's SocketIO server.
        Returning True stops polling for connection to succeed.
        """
        if self._exiting:
            return True

        self.sio.connect(self.settings.copilot_url, socketio_path="sio/socket.io")
        return True

    def open_camera(self):
        """
        Initialize camera and aruco markers detection parameters.
        """
        # List all detection parameters with their default values to help further optimization
        self._detector_params.adaptiveThreshWinSizeMin = 3
        self._detector_params.adaptiveThreshWinSizeMax = 23
        self._detector_params.adaptiveThreshWinSizeStep = 10
        self._detector_params.adaptiveThreshConstant = 7
        self._detector_params.minMarkerPerimeterRate = 0.03
        self._detector_params.maxMarkerPerimeterRate = 4.0
        self._detector_params.polygonalApproxAccuracyRate = 0.03
        self._detector_params.minCornerDistanceRate = 0.05
        self._detector_params.minDistanceToBorder = 3
        self._detector_params.minMarkerDistanceRate = 0.05
        self._detector_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_NONE
        self._detector_params.cornerRefinementWinSize = 5
        self._detector_params.cornerRefinementMaxIterations = 30
        self._detector_params.cornerRefinementMinAccuracy = 0.1
        self._detector_params.markerBorderBits = 1
        self._detector_params.perspectiveRemovePixelPerCell = 4
        self._detector_params.perspectiveRemoveIgnoredMarginPerCell = 0.13
        self._detector_params.maxErroneousBitsInBorderRate = 0.35
        self._detector_params.minOtsuStdDev = 5.0
        self._detector_params.errorCorrectionRate = 0.6
        self._detector_params.aprilTagMinClusterPixels = 5
        self._detector_params.aprilTagMaxNmaxima = 10
        self._detector_params.aprilTagCriticalRad = 10*math.pi/180
        self._detector_params.aprilTagMaxLineFitMse = 10.0
        self._detector_params.aprilTagMinWhiteBlackDiff = 5
        self._detector_params.aprilTagDeglitch = 0
        self._detector_params.aprilTagQuadDecimate = 0.0
        self._detector_params.aprilTagQuadSigma = 0.0
        self._detector_params.detectInvertedMarker = False

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
        try:
            while not self._exiting:
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

        except (KeyboardInterrupt, ExitSignal):
            pass

        logger.info("Camera handler: Exiting.")

        self.close_last_frame()
        self.close_camera()
        if self.sio.connected:
            self.sio.disconnect()

    def process_image(self) -> None:
        """
        Read one frame from camera, process it, send samples to Copilot
        and generate image to stream.
        """
        ret, image_color = self._camera_capture.read()
        if not ret:
            raise Exception("Camera handler: Cannot read frame.")

        image_stream = image_color

        image_gray = cv2.cvtColor(image_color, cv2.COLOR_BGR2GRAY)

        if not self.settings.calibration:
            image_stream = image_gray

        # Detect markers
        corners, ids, rejected = cv2.aruco.detectMarkers(
            image_gray,
            self._marker_dictionary,
            parameters=self._detector_params,
            cameraMatrix=self._camera_matrix_coefficients,
            distCoeff=self._camera_distortion_coefficients
        )

        # Draw a square around the markers
        cv2.aruco.drawDetectedMarkers(
            image_stream,
            corners=corners,
            ids=ids
        )

        # Record coords by marker id to sort them by id
        coords_by_id = {}

        if(np.any(ids)):
            # Estimate position of markers
            rvecs, tvecs, marker_points = cv2.aruco.estimatePoseSingleMarkers(
                corners,
                markerLength=50,
                cameraMatrix=self._camera_matrix_coefficients,
                distCoeffs=self._camera_distortion_coefficients
            )

            for (id, rvec, tvec) in zip(ids, rvecs, tvecs):
                # Convert marker position from local camera coordinates to world coordinates
                id = id[0]
                rvec = rvec[0]
                tvec = tvec[0]

                rvec_flipped = rvec * -1
                rotation_matrix, jacobian = cv2.Rodrigues(rvec_flipped)

                sy = math.sqrt(rotation_matrix[0, 0] * rotation_matrix[0, 0] + rotation_matrix[1, 0] * rotation_matrix[1, 0])

                if sy >= 1e-6:
                    rot_z = math.atan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
                else:
                    rot_z = 0

                # Draw axis
                cv2.aruco.drawAxis(
                    image_stream,
                    cameraMatrix=self._camera_matrix_coefficients,
                    distCoeffs=self._camera_distortion_coefficients,
                    rvec=rvec,
                    tvec=tvec,
                    length=25
                )

                coords_by_id[id.item()] = (*[v.item() for v in tvec], rot_z)

        if self.sio.connected:
            self.sio.emit("samples", coords_by_id)

        if not self.settings.calibration:
            # Print sample coords on image
            for i, (id, coords) in enumerate(sorted(coords_by_id.items())):
                tvec_str = (
                    f"[{id:2d}] "
                    f"X: {coords[0]: 4.0f} "
                    f"Y: {coords[1]: 4.0f} "
                    f"Z: {coords[2]: 4.0f} "
                    f"0: {math.degrees(coords[3]):3.1f}"
                )
                cv2.putText(
                    img=image_stream,
                    text=tvec_str,
                    org=(20, 465 - 20 * i),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=0.5,
                    color=(0, 0, 255),
                    thickness=2,
                    bottomLeftOrigin=False
                )
        elif sorted(list(coords_by_id.keys())) == list(range(6)):
            put_text = functools.partial(
                cv2.putText,
                img=image_stream,
                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=0.5,
                color=(0, 0, 255),
                thickness=1,
                bottomLeftOrigin=False
            )

            x0, y0, z0, rot0 = coords_by_id[0]
            x1, y1, z1, rot1 = coords_by_id[1]
            x2, y2, z2, rot2 = coords_by_id[2]
            x3, y3, z3, rot3 = coords_by_id[3]
            x4, y4, z4, rot4 = coords_by_id[4]
            x5, y5, z5, rot5 = coords_by_id[5]

            put_text(text="rot = ", org=(20, 20))
            put_text(text=f"{math.degrees(rot0):+3.1f}", org=(70, 20))
            put_text(text=f"{math.degrees(rot1):+3.1f}", org=(120, 20))
            put_text(text=f"{math.degrees(rot2):+3.1f}", org=(170, 20))
            put_text(text=f"{math.degrees(rot3):+3.1f}", org=(220, 20))
            put_text(text=f"{math.degrees(rot4):+3.1f}", org=(270, 20))
            put_text(text=f"{math.degrees(rot5):+3.1f}", org=(320, 20))

            put_text(text=f"dist(x0, x3) = {abs(x0 - x3):+3.0f}", org=(20, 50))
            put_text(text=f"dist(x1, x4) = {abs(x1 - x4):+3.0f}", org=(20, 70))
            put_text(text=f"dist(x2, x5) = {abs(x2 - x5):+3.0f}", org=(20, 90))

            put_text(text=f"dist(y0, y1) = {abs(y0 - y1):+3.0f}", org=(270, 60))
            put_text(text=f"dist(y1, y2) = {abs(y1 - y2):+3.0f}", org=(270, 80))

            put_text(text=f"dist(y3, y4) = {abs(y3 - y4):+3.0f}", org=(270, 110))
            put_text(text=f"dist(y4, y5) = {abs(y4 - y5):+3.0f}", org=(270, 130))

        # Encode the frame in BMP format (larger but faster than JPEG)
        ret, encoded_image = cv2.imencode(".bmp", image_stream)

        if not ret:
            raise Exception("Can't encode frame.")

        frame = (b'--frame\r\n' b'Content-Type: image/bmp\r\n\r\n' + encoded_image.tobytes() + b'\r\n')
        self.open_last_frame(len(frame))

        if self._last_frame:
            self._last_frame.buf[0:len(frame)] = frame

    def register_sio_events(self) -> None:
        @self.sio.event
        def connect():
            """
            Callback on Copilot connection.
            """
            logger.info("Camera handler: connected to Copilot")

        @self.sio.event
        def connect_error(data):
            """
            Callback on Copilot connection error.
            """
            logger.info("Camera handler: connection to Copilot failed.")

        @self.sio.event
        def disconnect():
            """
            Callback on Copilot disconnection.
            """
            logger.info("Camera handler: disconnected from Copilot")

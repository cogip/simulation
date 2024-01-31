from pathlib import Path
from typing import Annotated

import cv2
import cv2.aruco
import cv2.typing
import typer

from . import logger
from .arguments import CameraName, VideoCodec
from .utils import get_camera_intrinsic_params_filename, save_camera_intrinsic_params


def cmd_calibrate(
    ctx: typer.Context,
    id: Annotated[
        int,
        typer.Option(
            "-i",
            "--id",
            min=0,
            help="Robot ID.",
            envvar=["ROBOT_ID", "CAMERA_ID"],
        ),
    ] = 1,
    camera_name: Annotated[
        CameraName,
        typer.Option(
            help="Name of the camera",
            envvar="CAMERA_NAME",
        ),
    ] = CameraName.hbv.name,
    camera_codec: Annotated[
        VideoCodec,
        typer.Option(
            help="Camera video codec",
            envvar="CAMERA_CODEC",
        ),
    ] = VideoCodec.yuyv.name,
    camera_width: Annotated[
        int,
        typer.Option(
            help="Camera frame width",
            envvar="CAMERA_WIDTH",
        ),
    ] = 640,
    camera_height: Annotated[
        int,
        typer.Option(
            help="Camera frame height",
            envvar="CAMERA_HEIGHT",
        ),
    ] = 480,
    charuco_rows: Annotated[
        int,
        typer.Option(
            help="Number of rows on the Charuco board",
            envvar="CAMERA_CHARUCO_ROWS",
        ),
    ] = 13,
    charuco_cols: Annotated[
        int,
        typer.Option(
            help="Number of columns on the Charuco board",
            envvar="CAMERA_CHARUCO_COLS",
        ),
    ] = 8,
    charuco_marker_length: Annotated[
        int,
        typer.Option(
            help="Length of an Aruco marker on the Charuco board (in mm)",
            envvar="CAMERA_CHARUCO_MARKER_LENGTH",
        ),
    ] = 23,
    charuco_square_length: Annotated[
        int,
        typer.Option(
            help="Length of a square in the Charuco board (in mm)",
            envvar="CAMERA_CHARUCO_SQUARE_LENGTH",
        ),
    ] = 30,
    charuco_legacy: Annotated[
        bool,
        typer.Option(
            help="Use Charuco boards compatible with OpenCV < 4.6",
            envvar="CAMERA_CHARUCO_LEGACY",
        ),
    ] = False,
):
    """Calibrate camera using images captured by the 'capture' command"""
    obj = ctx.ensure_object(dict)
    debug = obj.get("debug", False)
    capture_path = Path(__file__).parent  # Directory to store captured frames
    capture_path /= f"cameras/{id}/{camera_name.name}_{camera_codec.name}_{camera_width}x{camera_height}/images"
    params_filename = get_camera_intrinsic_params_filename(id, camera_name, camera_codec, camera_width, camera_height)

    if not capture_path.exists():
        logger.error(f"Captured images directory not found: {capture_path}")
        return

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    board = cv2.aruco.CharucoBoard(
        (charuco_rows, charuco_cols),
        charuco_square_length,
        charuco_marker_length,
        aruco_dict,
    )
    if charuco_legacy:
        board.setLegacyPattern(True)

    captured_images = list(capture_path.glob("image_*.jpg"))
    if (nb_img := len(captured_images)) < 10:
        logger.error(f"Not enough images: {nb_img} < 10")
        return

    object_points = []
    image_points: list[cv2.typing.MatLike] = []

    board_detector = cv2.aruco.CharucoDetector(board)

    for im in sorted(captured_images)[0:]:
        frame = cv2.imread(str(im))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        char_corners, char_ids, _, _ = board_detector.detectBoard(gray)
        if char_corners is None or len(char_corners) == 0:
            logger.info(f"{im}: KO")
            continue
        logger.info(f"{im}: OK")
        frame_obj_points, frame_img_points = board.matchImagePoints(char_corners, char_ids)
        object_points.append(frame_obj_points)
        image_points.append(frame_img_points)

        if debug:
            cv2.aruco.drawDetectedCornersCharuco(frame, char_corners, char_ids)
            cv2.imshow("img", frame)
            cv2.waitKey(1000)

    ret, camera_matrix, dist_coefs, _, _ = cv2.calibrateCamera(
        object_points,
        image_points,
        (camera_width, camera_height),
        None,
        None,
    )

    logger.debug(f"Camera calibration status: {ret}")
    logger.debug("- camera matrix:")
    logger.debug(camera_matrix)
    logger.debug("- dist coefs:")
    logger.debug(dist_coefs)

    save_camera_intrinsic_params(camera_matrix, dist_coefs, params_filename)
    logger.info(f"Calibration parameters stored in: {params_filename}")

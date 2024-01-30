import logging
from pathlib import Path
from typing import Annotated, Optional

import cv2
import typer
import v4l2py

from . import logger
from .arguments import CameraName, VideoCodec


def cmd_info(
    ctx: typer.Context,
    camera_name: Annotated[
        Optional[CameraName],  # noqa
        typer.Option(
            help="Name of the camera (all if not specified)",
            envvar="CAMERA_NAME",
        ),
    ] = None,
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
):
    """Get properties of connected cameras"""
    obj = ctx.ensure_object(dict)
    debug = obj.get("debug", False)

    if debug:
        v4l2py.device.log.setLevel(logging.DEBUG)
    else:
        v4l2py.device.log.setLevel(logging.INFO)

    if camera_name:
        if not Path(camera_name.val).exists():
            logger.error(f"Camera not found: {camera_name}")
            return
        device = v4l2py.Device(camera_name.val)
        try:
            device.open()
        except OSError:
            logger.error(f"Failed to open {camera_name.val}")
            return
        print_device_info(device)
        device.close()
        show_stream(camera_name, camera_codec, camera_width, camera_height)
        return

    for device in v4l2py.iter_video_capture_devices():
        try:
            device.open()
        except OSError:
            pass
        else:
            print_device_info(device)
            device.close()
            print()


def print_device_info(device: v4l2py.device.Device):
    logger.info(f"Camera: {device.filename} ({device.info.card})")

    if not device.info:
        logger.warning("  - No device info")
        return

    logger.info("  - Frame sizes:")
    frame_sizes: set[tuple[v4l2py.device.PixelFormat, int, int]] = set()
    for frame_size in device.info.frame_sizes:
        frame_size: v4l2py.device.FrameType
        frame_sizes.add((frame_size.pixel_format, frame_size.width, frame_size.height))

    for pixel_format, width, height in sorted(frame_sizes):
        logger.info(f"    - {pixel_format.name:>5s} - {width:4d} x {height:4d}")

    logger.info("  - Available controls:")
    for control in device.controls.values():
        match type(control):
            case v4l2py.device.BooleanControl:
                logger.info(f"    - {control.name} - value={control.value} - default={control.default}")
            case v4l2py.device.IntegerControl:
                logger.info(
                    f"    - {control.name} - value={control.value} - default={control.default}"
                    f" - min={control.minimum} - max={control.maximum}"
                )
            case v4l2py.device.MenuControl:
                logger.info(f"    - {control.name} - value={control.value} - default={control.default}")
                for key, value in control.data.items():
                    logger.info(f"      - {key}: {value}")

    logger.info("")


def show_stream(name: CameraName, codec: VideoCodec, width: int, height: int):
    exit_key = 27  # Use this key (Esc) to exit stream display
    window_name = "Stream Preview - Press Esc to exit"

    cap = cv2.VideoCapture(str(name.val))

    fourcc = cv2.VideoWriter_fourcc(*codec.val)
    ret = cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    if not ret:
        logger.warning(f"Video codec {codec.val} not supported")

    ret = cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if not ret:
        logger.warning(f"Frame width {width} not supported")

    ret = cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if not ret:
        logger.warning(f"Frame height {height} not supported")

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_EXPANDED)

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Cannot read current frame.")

        cv2.imshow(window_name, frame)

        k = cv2.waitKey(1)
        if k == exit_key:
            break

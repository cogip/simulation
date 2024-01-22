from typing import TYPE_CHECKING

import httpx

from . import logger
from .camp import Camp
from cogip.models.models import Vertex

if TYPE_CHECKING:
    from .robot import Robot


async def snapshot():
    camp = Camp().color.value
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://localhost:8100/snapshots?camp={camp}")
            if response.status_code != 200:
                logger.warning(f"Request snapshot: Failed: {response.status_code}: {response.text}")
        except httpx.HTTPError as exc:
            logger.error(f"Request snapshot: HTTP Exception: {exc}")



async def calibrate_camera(robot: "Robot") -> Vertex | None:
    async with httpx.AsyncClient() as client:
        try:
            port = 8100 + robot.robot_id
            queries = f"x={robot.pose_current.x}"
            queries += f"&y={robot.pose_current.y}"
            queries += f"&angle={robot.pose_current.O}"
            response = await client.get(f"http://robot{robot.robot_id}:{port}/camera_calibration?{queries}")
            if response.status_code != 200:
                logger.warning(f"Request camera_calibration: Failed: {response.status_code}: {response.text}")
                return None
            return Vertex.model_validate(response.json())
        except httpx.HTTPError as exc:
            logger.error(f"Request camera_calibration: HTTP Exception: {exc}")
            return None
        except Exception as exc:  # noqa
            logger.error(f"Request camera_calibration: Unknown exception: {exc}")
            return None

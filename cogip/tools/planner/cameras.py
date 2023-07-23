import httpx

from cogip.models.artifacts import CakeSlotID
from . import logger
from .camp import Camp


async def snapshot():
    camp = Camp().color.value
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://localhost:8090/snapshots?camp={camp}")
            if response.status_code != 200:
                logger.warning(f"Request snapshot: Failed: {response.status_code}: {response.text}")
        except httpx.HTTPError as exc:
            logger.error(f"Request snapshot: HTTP Exception: {exc}")


def is_cake_in_slot(slot: CakeSlotID) -> bool:
    camp = Camp().color.value
    try:
        response = httpx.get(f"http://localhost:8090/check?camp={camp}&slot={slot.value}")
        if response.status_code != 200:
            logger.warning(f"Request cake_in_slot {slot.name} failed: {response.status_code}: {response.text}")
            return False
        res = response.json()
        logger.debug(f"Beacon: cake_in_slot({slot.name})={res}")
        return res
    except httpx.HTTPError as exc:
        logger.error(f"Request cake_in_slot {slot.name} failed: {exc}")
        return False


async def is_cherry_on_cake(robot_id: int) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://robot{robot_id}:808{robot_id}/cherry_on_cake")
            if response.status_code != 200:
                logger.warning(f"Request cherry_on_cake failed: {response.status_code}: {response.text}")
                return False
            res = response.json()
            logger.debug(f"Robot {robot_id}: cherry_on_cake={res}")
            return res
        except httpx.HTTPError as exc:
            logger.error(f"Request cherry_on_cake {robot_id} failed: {exc}")
            return False

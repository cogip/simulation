import httpx

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

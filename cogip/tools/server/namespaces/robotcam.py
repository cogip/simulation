from bidict import bidict
import socketio

from .. import logger

robotcam_sids = bidict()  # map Robotcam sid (str) to robot id (int)


class RobotcamNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to robotcam.
    """
    def __init__(self):
        super().__init__("/robotcam")
        self._robotcam_sid: str | None = None

    async def on_connect(self, sid, environ):
        if self._robotcam_sid:
            logger.error("Connection refused: a robotcam is already connected")
            raise ConnectionRefusedError("A robotcam is already connected")
        self._robotcam_sid = sid
        logger.info("Robotcam connected.")

    def on_disconnect(self, sid):
        self._robotcam_sid = None
        logger.info("Robotcam disconnected.")

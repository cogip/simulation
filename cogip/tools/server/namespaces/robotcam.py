import socketio
from bidict import bidict

from .. import logger

robotcam_sids = bidict()  # map Robotcam sid (str) to robot id (int)


class RobotcamNamespace(socketio.AsyncNamespace):
    """
    Handle all SocketIO events related to robotcam.
    """

    def __init__(self):
        super().__init__("/robotcam")

    async def on_connect(self, sid, environ, auth={}):
        if isinstance(auth, dict) and (robot_id := auth.get("id")):
            if sid not in robotcam_sids and robot_id in robotcam_sids.inverse:
                logger.error(f"A robotcam with id '{robot_id}' seems already connected, cleaning up")
                old_sid = robotcam_sids.inverse[robot_id]
                self.on_disconnect(old_sid)
            robotcam_sids[sid] = robot_id
        else:
            raise ConnectionRefusedError("Missing 'id' in 'auth' parameter")

    async def on_connected(self, sid, robot_id: int):
        logger.info(f"Robotcam {robot_id} connected.")

    def on_disconnect(self, sid):
        if sid in robotcam_sids:
            robot_id = robotcam_sids.pop(sid)
            logger.info(f"Robotcam {robot_id} disconnected.")
        else:
            logger.warning(f"Robotcam: attempt to disconnect with unknown sid {sid}.")

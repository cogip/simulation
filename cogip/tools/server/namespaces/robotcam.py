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

    async def on_connect(self, sid, environ, auth={}):
        if isinstance(auth, dict) and (robot_id := auth.get("id")):
            if sid not in robotcam_sids and robot_id in robotcam_sids.inverse:
                raise ConnectionRefusedError(f"A robotcam with id '{robot_id}' is already connected")
            robotcam_sids[sid] = robot_id
            logger.info(f"Robotcam {robot_id} connected.")
        else:
            raise ConnectionRefusedError("Missing 'id' in 'auth' parameter")

    def on_disconnect(self, sid):
        robot_id = robotcam_sids.pop(sid)
        logger.info(f"Robotcam {robot_id} disconnected.")

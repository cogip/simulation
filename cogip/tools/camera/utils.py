from pathlib import Path

import cv2
import cv2.typing


#
# Utility functions to handle calibration parameters
#

def get_camera_intrinsic_params_filename(
        robot_id: int,
        name: CameraName,
        codec: VideoCodec,
        width: int,
        height: int) -> Path:
    """ Get parameters filename based on current package path and camera parameters """
    params_filename = Path(__file__).parent
    params_filename /= f"cameras/{robot_id}/{name.name}_{codec.name}_{width}x{height}/intrinsic_params.yaml"
    return params_filename


def save_camera_intrinsic_params(camera_matrix: cv2.typing.MatLike, dist_coefs: cv2.typing.MatLike, path: Path):
    """ Save the camera matrix and the distortion coefficients to given path/file. """
    cv_file = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    cv_file.write("K", camera_matrix)
    cv_file.write("D", dist_coefs)
    cv_file.release()

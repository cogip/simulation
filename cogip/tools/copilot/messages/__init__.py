from pathlib import Path
import sys

# Generated Protobuf messages includes required messages
# as if the current directory was the root of a package.
# So add this directory to Python paths to allow the import.
sys.path.insert(0, str(Path(__file__).parent.absolute()))


from .PB_Color_pb2 import PB_Color  # noqa
from .PB_Pose_pb2 import PB_Pose  # noqa
from .PB_Menu_pb2 import PB_Menu  # noqa
from .PB_Command_pb2 import PB_Command  # noqa
from .PB_State_pb2 import PB_State  # noqa
from .PB_Score_pb2 import PB_Score  # noqa
from .PB_Obstacles_pb2 import PB_Obstacles  # noqa
from .PB_PathPose_pb2 import PB_PathPose  # noqa
from .PB_SpeedEnum_pb2 import PB_SpeedEnum  # noqa

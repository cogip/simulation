from dataclasses import dataclass, field
from typing import Dict, List, Literal

from bidict import bidict

from cogip import models
from cogip.utils.singleton import Singleton


@dataclass
class Context(metaclass=Singleton):
    """
    Server context class recording variables using in multiple namespaces.

    Attributes:
        copilot_sids:       map Copilot sid (str) to robot id (int)
        detector_sids:      map Detector sid (str) to robot id (int)
        detector_modes:     map robot id to Detector mode
        robotcam_sids:      map Robotcam sid (str) to robot id (int)
        tool_menus:         all registered tool menus
        current_tool_menu:  name of the currently selected tool menu
        shell_menu:         last received shell menu
        connected_robots:   list of robots already connected
    """
    copilot_sids = bidict()
    detector_sids = bidict()
    detector_modes: Dict[int, Literal["detection", "emulation"]] = field(default_factory=dict)
    robotcam_sids = bidict()
    tool_menus: Dict[str, models.ShellMenu] = field(default_factory=dict)
    current_tool_menu: str | None = None
    shell_menu: Dict[int, models.ShellMenu] = field(default_factory=dict)
    connected_robots: List[int] = field(default_factory=list)

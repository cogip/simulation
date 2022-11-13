from dataclasses import dataclass, field
from typing import Dict, Literal

from cogip import models
from cogip.utils.singleton import Singleton


@dataclass
class Context(metaclass=Singleton):
    """
    Server context class recording variables using in multiple namespaces.

    Attributes:
        detector_mode:      Detector mode (detection or emulation)
        tool_menus:         all registered tool menus
        current_tool_menu:  name of the currently selected tool menu
        shell_menu:         last received shell menu
    """
    detector_mode: Literal["detection", "emulation"] | None = None
    tool_menus: Dict[str, models.ShellMenu] = field(default_factory=dict)
    current_tool_menu: str | None = None
    shell_menu: Dict[int, models.ShellMenu] = field(default_factory=dict)

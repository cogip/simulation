from dataclasses import dataclass, field
from typing import Dict, Literal

from cogip import models
from cogip.utils.singleton import Singleton


@dataclass
class Context(metaclass=Singleton):
    """
    Server context class recording variables using in multiple namespaces.

    Attributes:
        detector_mode:  Detector mode (detection or emulation)
        planner_menu:   last received planner menu
        shell_menu:     last received shell menu
    """
    detector_mode: Literal["detection", "emulation"] | None = None
    planner_menu: models.ShellMenu | None = None
    shell_menu: Dict[int, models.ShellMenu] = field(default_factory=dict)

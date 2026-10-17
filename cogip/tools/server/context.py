import platform
from dataclasses import dataclass, field

from cogip import models
from cogip.utils.singleton import Singleton

# Context attributes holding the last power supply states, named after the events that carry them
POWER_SUPPLY_STATE_NAMES = (
    "emergency_stop_status",
    "power_source_status",
    "power_rails_status",
    "power_rails_measures",
)


@dataclass
class Context(metaclass=Singleton):
    """
    Server context class recording variables using in multiple namespaces.

    Attributes:
        robot_id:               Robot ID
        planner_sid:            Planner sid
        copilot_sid:            Copilot sid
        detector_sid:           Detector sid
        robotcam_sid:           Robotcam sid
        beacon_sid:             Beacon server sid
        monitor_sid:            Monitor sid
        calibration_sid:        Calibration client sid
        tool_menus:             all registered tool menus
        current_tool_menu:      name of the currently selected tool menu
        shell_menu:             last received shell menu
        virtual:                Whether robot is virtual or not
        virtual_planner:        Whether planner is virtual or not
        virtual_detector:       Whether detector is virtual or not
        robot_added:            Whether robot has been added or not
        emergency_stop_status:  last received emergency stop status
        power_source_status:    last received power source status
        power_rails_status:     last received power rails status
        power_rails_measures:   last received power rails measures
    """

    robot_id: int | None = None
    planner_sid: str | None = None
    copilot_sid: str | None = None
    detector_sid: str | None = None
    robotcam_sid: str | None = None
    beacon_sid: str | None = None
    monitor_sid: str | None = None
    calibration_sid: str | None = None
    tool_menus: dict[str, models.ShellMenu] = field(default_factory=dict)
    current_tool_menu: str | None = None
    shell_menu: models.ShellMenu | None = None
    virtual = platform.machine() != "aarch64"
    virtual_planner = False
    virtual_detector = False
    robot_added = False
    emergency_stop_status: models.EmergencyStopStatus | None = None
    power_source_status: models.PowerSourceStatus | None = None
    power_rails_status: models.PowerRailsStatus | None = None
    power_rails_measures: models.PowerRailsMeasures | None = None

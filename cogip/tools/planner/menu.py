from cogip import models


menu = models.ShellMenu(
    name="Planner",
    entries=[
        models.MenuEntry(cmd="game_wizard", desc="Wizard"),
        models.MenuEntry(cmd="choose_camp", desc="Choose camp"),
        models.MenuEntry(cmd="choose_strategy", desc="Choose strategy"),
        models.MenuEntry(cmd="choose_avoidance", desc="Choose avoidance"),
        models.MenuEntry(cmd="choose_table", desc="Choose table"),
        models.MenuEntry(cmd="play", desc="Play"),
        models.MenuEntry(cmd="stop", desc="Stop"),
        models.MenuEntry(cmd="next", desc="Next"),
        models.MenuEntry(cmd="reset", desc="Reset"),
        models.MenuEntry(cmd="config", desc="Configuration")
    ]
)

wizard_test_menu = models.ShellMenu(
    name="Wizard Test",
    entries=[
        models.MenuEntry(cmd="wizard_boolean", desc="Boolean"),
        models.MenuEntry(cmd="wizard_integer", desc="Integer"),
        models.MenuEntry(cmd="wizard_floating", desc="Float"),
        models.MenuEntry(cmd="wizard_str", desc="String"),
        models.MenuEntry(cmd="wizard_message", desc="Message"),
        models.MenuEntry(cmd="wizard_choice_integer", desc="Choice Integer"),
        models.MenuEntry(cmd="wizard_choice_floating", desc="Choice Float"),
        models.MenuEntry(cmd="wizard_choice_str", desc="Choice String"),
        models.MenuEntry(cmd="wizard_select_integer", desc="Select Integer"),
        models.MenuEntry(cmd="wizard_select_floating", desc="Select Float"),
        models.MenuEntry(cmd="wizard_select_str", desc="Select String"),
        models.MenuEntry(cmd="wizard_camp", desc="Camp"),
        models.MenuEntry(cmd="wizard_camera", desc="Camera"),
        models.MenuEntry(cmd="wizard_score", desc="Score")
    ]
)

cameras_menu = models.ShellMenu(
    name="Cameras",
    entries=[
        models.MenuEntry(cmd="cam_beacon_snapshots", desc="Beacon Snapshot")
    ]
)

actuators_commands = [
    "pump_left_on",
    "pump_left_off",
    "pump_right_on",
    "pump_right_off",
    "left_arm_folded",
    "left_arm_extended",
    "right_arm_folded",
    "right_arm_extended",
    "led_off",
    "led_on",
    "central_arm_up",
    "central_arm_down",
    "left_arm_up",
    "left_arm_down",
    "right_arm_up",
    "right_arm_down"
]

actuators_menu_1 = models.ShellMenu(
    name="Actuators 1",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}_1", desc=f"{cmd.replace('_', ' ').title()}")
        for cmd in actuators_commands
    ]
)

actuators_menu_2 = models.ShellMenu(
    name="Actuators 2",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}_2", desc=f"{cmd.replace('_', ' ').title()}")
        for cmd in actuators_commands
    ]
)


cherries_commands = [
    "action_deliver_on_cake",
    "action_launch_start",
    "action_launch_stop",
    "action_aspirate_start",
    "action_aspirate_stop",
    "cherry_switch_closed",
    "cherry_switch_cake",
    "cherry_switch_launcher",
    "cherry_arm_up",
    "cherry_arm_down",
    "cherry_esc_off",
    "cherry_esc_on",
    "cherry_esc_eject",
    "cherry_release_down",
    "cherry_release_up",
    "cherry_conveyor_on",
    "cherry_conveyor_off",
]

cherries_menu_1 = models.ShellMenu(
    name="Cherries 1",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}_1", desc=f"{cmd.replace('_', ' ').title()}")
        for cmd in cherries_commands
    ]
)

cherries_menu_2 = models.ShellMenu(
    name="Cherries 2",
    entries=[
        models.MenuEntry(cmd=f"act_{cmd}_2", desc=f"{cmd.replace('_', ' ').title()}")
        for cmd in cherries_commands
    ]
)

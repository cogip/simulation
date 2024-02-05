from cogip import models

menu = models.ShellMenu(
    name="Copilot",
    entries=[
        models.MenuEntry(cmd="actuators_control", desc="Actuators Control"),
        models.MenuEntry(cmd="angular_speed_pid_config", desc="Angular Speed PID Config"),
        models.MenuEntry(cmd="linear_speed_pid_config", desc="Linear Speed PID Config"),
        models.MenuEntry(cmd="angular_position_pid_config", desc="Angular Position PID Config"),
        models.MenuEntry(cmd="linear_position_pid_config", desc="Linear Position PID Config"),
    ],
)

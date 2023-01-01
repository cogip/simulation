from cogip import models


menu = models.ShellMenu(
    name="Copilot",
    entries=[
        models.MenuEntry(cmd="actuators_control", desc="Actuators Control")
    ]
)

from cogip import models


menu = models.ShellMenu(
    name="Avoidance",
    entries=[
        models.MenuEntry(cmd="config", desc="Configuration")
    ]
)

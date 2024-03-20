from cogip import models

menu = models.ShellMenu(
    name="Beacon",
    entries=[
        models.MenuEntry(cmd="reset", desc="Reset"),
        models.MenuEntry(cmd="start", desc="Start"),
    ],
)

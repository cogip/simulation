from cogip import models

menu = models.ShellMenu(
    name="Detector",
    entries=[
        models.MenuEntry(cmd="config", desc="Configuration"),
    ],
)

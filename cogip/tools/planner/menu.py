from cogip import models


menu = models.ShellMenu(
    name="Planner",
    entries=[
        models.MenuEntry(cmd="play", desc="Play full path"),
        models.MenuEntry(cmd="stop", desc="Stop playing path"),
        models.MenuEntry(cmd="next", desc="Next position"),
        models.MenuEntry(cmd="prev", desc="Previous position"),
        models.MenuEntry(cmd="reset", desc="Reset to start position"),
    ]
)

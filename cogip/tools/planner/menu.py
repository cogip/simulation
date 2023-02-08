from cogip import models


menu = models.ShellMenu(
    name="Planner",
    entries=[
        models.MenuEntry(cmd="choose_camp", desc="Choose camp"),
        models.MenuEntry(cmd="choose_strategy", desc="Choose strategy"),
        models.MenuEntry(cmd="play", desc="Play"),
        models.MenuEntry(cmd="stop", desc="Stop"),
        models.MenuEntry(cmd="next", desc="Next"),
        models.MenuEntry(cmd="reset", desc="Reset")
    ]
)

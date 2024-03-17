from cogip import models

menu = models.ShellMenu(
    name="Beacon",
    entries=[
        models.MenuEntry(cmd="choose_camp", desc="Choose camp"),
        models.MenuEntry(cmd="choose_table", desc="Choose table"),
        models.MenuEntry(cmd="reset", desc="Reset"),
        models.MenuEntry(cmd="start", desc="Start"),
    ],
)

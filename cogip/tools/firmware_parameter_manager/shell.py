"""Interactive shell for the firmware parameter manager.

Provides tab-completed `list` / `get` / `set` / `reset` / `reset-all` commands
over the parameters discovered from the firmware.
"""

import asyncio
import readline
import shlex

from pydantic import ValidationError

from cogip.models import FirmwareParameter
from cogip.utils.console_ui import ConsoleUI
from .firmware_parameter_manager import FirmwareParameterManager

PROMPT = "fw-param> "
COMMANDS = ("list", "get", "set", "reset", "reset-all", "help", "exit", "quit")
NAME_COMMANDS = ("get", "set", "reset")
TIMEOUT = 2.0


def parse_value(parameter: FirmwareParameter, raw_value: str) -> float | int | bool:
    """Convert a string to the type of a parameter."""
    match parameter.value_obj.type:
        case "bool":
            if raw_value.lower() in ("1", "true", "yes", "on"):
                return True
            if raw_value.lower() in ("0", "false", "no", "off"):
                return False
            raise ValueError(f"invalid bool value: {raw_value!r}")
        case "float" | "double":
            return float(raw_value)
        case _:
            return int(raw_value)


def format_value(value: float | int | bool | Exception) -> str:
    if isinstance(value, Exception):
        return f"<{type(value).__name__}>"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


class ParameterCompleter:
    """readline completer for `<command> [<parameter>]`."""

    def __init__(self, manager: FirmwareParameterManager):
        self.manager = manager
        self.matches: list[str] = []

    def __call__(self, text: str, state: int) -> str | None:
        if state == 0:
            tokens = readline.get_line_buffer()[: readline.get_begidx()].split()
            if not tokens:
                words = COMMANDS
            elif tokens[0] in NAME_COMMANDS and len(tokens) == 1:
                words = self.manager.parameters
            else:
                words = ()
            self.matches = [word for word in words if word.startswith(text)]
        return self.matches[state] if state < len(self.matches) else None


async def _list(manager: FirmwareParameterManager, ui: ConsoleUI) -> None:
    """Discover the parameters, then show the value and range of each one, by registry."""
    await manager.discover(TIMEOUT)
    if not manager.registries:
        ui.show_warning("no parameter registry discovered")
        return

    names = list(manager.parameters)
    values = await asyncio.gather(
        *(manager.get_parameter_value(name, TIMEOUT) for name in names),
        return_exceptions=True,
    )
    results = dict(zip(names, values))

    table = ui.create_table(
        columns=[
            ("Parameter", {"style": "label", "no_wrap": True}),
            ("Value", {"style": "value", "justify": "right", "no_wrap": True}),
            ("Range", {"style": "muted", "no_wrap": True}),
        ],
    )
    for index, (registry_name, registry) in enumerate(manager.registries.items()):
        if index > 0:
            table.add_section()
        table.add_row(f"[phase]{registry_name}[/]", "", "")
        for parameter in registry:
            table.add_row(
                f"  {parameter.name}",
                format_value(results[parameter.name]),
                f"[{format_value(parameter.value_obj.min)}, {format_value(parameter.value_obj.max)}]",
            )
    ui.print(table)


async def _reset_all(manager: FirmwareParameterManager, ui: ConsoleUI) -> None:
    names = list(manager.parameters)
    errors = await asyncio.gather(
        *(manager.reset_parameter_value(name, TIMEOUT) for name in names),
        return_exceptions=True,
    )
    for name, error in zip(names, errors):
        if error:
            ui.show_error(f"{name}: {error}")
    ui.show_success(f"{errors.count(None)}/{len(names)} parameters reset")


def _show_help(ui: ConsoleUI) -> None:
    ui.show_panel(
        "[label]list[/]                       discover and display every parameter\n"
        "[label]get <name>[/]                 read the current value from firmware\n"
        "[label]set <name> <value>[/]         write a new value\n"
        "[label]reset <name>[/]               restore the compile-time default\n"
        "[label]reset-all[/]                  reset every parameter\n"
        "[label]help[/]                       show this message\n"
        "[label]exit[/] | [label]quit[/] | [label]Ctrl-D[/]         leave the shell",
        title="Commands",
    )


async def _run_command(manager: FirmwareParameterManager, ui: ConsoleUI, line: str) -> None:
    """Run a command line and report its error, if any."""
    try:
        tokens = shlex.split(line)
        if not tokens:
            return

        match tokens:
            case ["list"]:
                await _list(manager, ui)
            case ["get", name]:
                value = await manager.get_parameter_value(name, TIMEOUT)
                ui.show_key_value_table([(name, format_value(value))])
            case ["set", name, raw_value]:
                value = parse_value(manager.parameters[name], raw_value)
                await manager.set_parameter_value(name, value, TIMEOUT)
                ui.show_success(f"{name} = {format_value(value)}")
            case ["reset", name]:
                await manager.reset_parameter_value(name, TIMEOUT)
                ui.show_success(f"{name} reset to default")
            case ["reset-all"]:
                await _reset_all(manager, ui)
            case ["help"]:
                _show_help(ui)
            case _:
                ui.show_error(f"invalid command: {line.strip()!r}. Type 'help' for the list.")
    except KeyError as exc:
        ui.show_error(f"unknown parameter: {exc.args[0]!r}")
    except ValidationError as exc:
        ui.show_error(f"invalid value: {exc.errors()[0]['msg']}")
    except Exception as exc:
        ui.show_error(str(exc))


async def run(manager: FirmwareParameterManager, ui: ConsoleUI) -> None:
    """Run the interactive shell until the user exits."""
    # Python's readline may be backed by libedit (macOS), which takes another binding syntax
    readline.set_completer_delims(" \t\n")
    if "libedit" in (readline.__doc__ or ""):
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    readline.set_completer(ParameterCompleter(manager))

    ui.show_panel(
        "Firmware parameter manager — interactive shell.\n"
        "Type [label]help[/] for the command list, [label]Tab[/] to complete.",
        title="firmware-parameter-manager",
    )
    await _run_command(manager, ui, "list")

    while True:
        try:
            line = await asyncio.to_thread(input, PROMPT)
        except EOFError:
            ui.print()
            break
        except KeyboardInterrupt:
            ui.print()
            continue
        if line.strip() in ("exit", "quit"):
            break
        await _run_command(manager, ui, line)

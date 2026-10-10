"""The obstacles the preview seeds.

The tool owns its shared memory segment, so it has to put something in it, and what it puts there
is this year's table: the fixed obstacles, the collection areas and the pantries, taken from the
planner's own :class:`GameContext` rather than transcribed. Transcribing them would leave the
preview showing last year's table the first time the rules change, which is the one thing it must
not do.

Two differences from what the planner writes, both deliberate:

- the dimensions are the **raw** ones. The planner adds ``robot_width`` to every side because its
  obstacles carry their own inflation; here inflation is the ``rho`` slider, applied by the graph
  builder as ``corner_radius += rho``. Baking it in twice would double it.
- one extra obstacle, a disc standing for a robot, which is the one the mouse drags.
"""

from dataclasses import dataclass

from cogip.cpp.libraries.shared_memory import SharedProperties
from cogip.tools.planner.context import GameContext
from cogip.tools.planner.table import Table


@dataclass
class Fixture:
    """One seeded obstacle."""

    name: str


@dataclass
class Circle(Fixture):
    x: float
    y: float
    radius: float
    draggable: bool = False
    """Whether the mouse may move this one. True for the robot, and nothing else."""


@dataclass
class Rectangle(Fixture):
    x: float
    y: float
    angle: float
    length_x: float
    length_y: float


#: Radius of the dragged disc, mm.
#:
#: The radius the detector gives a robot it sees, so the thing being dragged is the same obstacle
#: the avoidance would be routing around during a match.
ROBOT_RADIUS = 150.0

#: Where the dragged disc starts, mm.
#:
#: Chosen by measurement rather than by eye: at the default inflation this year's table leaves very
#: little room, and a disc dropped in the wrong place has every one of its nodes swallowed by a
#: neighbour — which looks exactly like the drag being broken. This is the most open spot in the
#: lower corridor, which is also where the graph is densest, so moving it visibly reorganises
#: something.
ROBOT_START = (-100.0, -800.0)


def robot() -> Circle:
    """The disc the mouse drags."""
    return Circle(name="robot", x=ROBOT_START[0], y=ROBOT_START[1], radius=ROBOT_RADIUS, draggable=True)


def game_obstacles(properties: SharedProperties, table: Table) -> list[Fixture]:
    """This year's obstacles, as the planner would place them.

    The angle and dimension mapping of each family mirrors ``Planner.update_obstacles()``, the swap
    of length and width on the fixed obstacles included — it is theirs, not a slip here.
    """
    context = GameContext(properties)
    fixtures: list[Fixture] = []

    for area in context.collection_areas.values():
        if not area.enabled or not table.contains(area):
            continue
        fixtures.append(
            Rectangle(
                name=f"area {area.id.name}",
                x=area.x,
                y=area.y,
                angle=area.O,
                length_x=area.length,
                length_y=area.width,
            )
        )

    for pantry in context.pantries.values():
        if not pantry.enabled or not table.contains(pantry):
            continue
        fixtures.append(
            Rectangle(
                name=f"pantry {pantry.id.name}",
                x=pantry.x,
                y=pantry.y,
                angle=pantry.O,
                length_x=pantry.length,
                length_y=pantry.width,
            )
        )

    for fixed in context.fixed_obstacles.values():
        if not fixed.enabled or not table.contains(fixed):
            continue
        fixtures.append(
            Rectangle(
                name=f"fixed {fixed.id.name}",
                x=fixed.x,
                y=fixed.y,
                angle=0.0,
                length_x=fixed.width,
                length_y=fixed.length,
            )
        )

    return fixtures

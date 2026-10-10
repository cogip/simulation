"""Shared memory side of the preview.

The tool is the owner of its segment: nothing else has to be running, and the obstacles it draws
are the ones it seeded. The graph itself is built in C++, in place, and read back as numpy views of
the same memory — which is what keeps a slider drag, or a dragged obstacle, responsive: nothing is
copied or marshalled between the build and the paint.
"""

from dataclasses import dataclass
from time import perf_counter

import numpy as np

from cogip.cpp.libraries.graph import Graph, sample_inflated_outline, sample_nodes
from cogip.cpp.libraries.shared_memory import LockName, SharedMemory
from cogip.tools.planner.table import Table, TableEnum
from . import logger
from .fixtures import Circle, Fixture, Rectangle, game_obstacles, robot


@dataclass
class Obstacle:
    """One obstacle, as the view needs it to draw the raw shape.

    The boundary comes from the C++ sampler with an inflation radius of zero, so a disc really is
    drawn round and a rounded polygon really is drawn rounded, without the view owning a second
    copy of the geometry.
    """

    id: int
    name: str
    boundary: list[tuple[float, float]]
    center: tuple[float, float]
    radius: float = 0.0
    """Pick radius of a draggable obstacle, mm. Zero for the ones that stay put."""

    @property
    def draggable(self) -> bool:
        return self.radius > 0.0


@dataclass
class GraphSnapshot:
    """The result of one build, as the view consumes it.

    The three arrays are *views* into shared memory, valid until the next build. The view repaints
    from them directly and must not outlive the build that produced them.
    """

    nodes: np.ndarray
    """(n, 2) float64 node coordinates, mm."""

    edges: np.ndarray
    """(m, 2) uint16 pairs of node indices."""

    hulls: list[np.ndarray]
    """One (k, 2) float64 polyline per inflated obstacle: the exact grown boundary."""

    rings: list[np.ndarray]
    """One (k, 2) float64 polygon per obstacle: the circumscribed ring at the current corner count.

    The unfiltered ring, so it closes even where a node was dropped for sitting inside a
    neighbour. This is the shape that changes with the corner count, and the only approximation
    anywhere in the obstacle stack — which is why it is worth drawing next to the exact boundary
    rather than leaving the nodes as loose dots.
    """

    build_time: float
    """Wall clock time of the build, seconds."""

    effective_limits: tuple[float, float, float, float]
    """The table, shrunk by the grown walls: (min_x, min_y, max_x, max_y) in mm."""

    nodes_truncated: bool
    edges_truncated: bool


class GraphPreviewMemory:
    """Owns the segment, seeds the obstacles, and drives the C++ graph builder."""

    def __init__(self, name: str, table: Table, table_enum: TableEnum, robot_id: int, table_margin: float):
        self.table = table
        self.table_margin = table_margin

        # Owner: the segment is created here and unlinked when this object goes away.
        self.shared_memory = SharedMemory(name, owner=True)

        self.shared_properties = self.shared_memory.get_properties()
        self.shared_table_limits = self.shared_memory.get_table_limits()
        self.shared_obstacles = self.shared_memory.get_obstacles_new()
        self.shared_params = self.shared_memory.get_graph_params()
        self.graph_lock = self.shared_memory.get_lock(LockName.Graph)

        # GameContext reads these to decide which obstacles exist and where, so they have to be set
        # before it is built. A fresh segment is zeroed, and robot_id 0 belongs to no robot.
        self.shared_properties.robot_id = robot_id
        self.shared_properties.table = table_enum.val

        # The order the rest of the stack uses: x_min, x_max, y_min, y_max.
        self.shared_table_limits[0] = table.x_min
        self.shared_table_limits[1] = table.x_max
        self.shared_table_limits[2] = table.y_min
        self.shared_table_limits[3] = table.y_max

        self.obstacles: list[Obstacle] = []
        self.robot: Obstacle | None = None
        self._seed(table_enum)

        self.graph = Graph(
            self.shared_memory.get_obstacles_new_data(),
            self.shared_params,
            self.shared_memory.get_graph_nodes(),
            self.shared_memory.get_graph_edges(),
            self.shared_memory.get_graph_hulls(),
        )

    def _seed(self, table_enum: TableEnum) -> None:
        """Write the fixtures into shared memory and snapshot what the view needs of them."""
        self.shared_obstacles.clear()
        self.obstacles = []

        # The robot goes last so it owns the highest index, which is also the one the display
        # outlines are keyed on. Nothing depends on the order, but a stable one makes a log
        # readable.
        for fixture in [*game_obstacles(self.shared_properties, self.table), robot()]:
            index = self._append(fixture)
            obstacle = self.shared_obstacles[index]
            # The factories do not set an id, and the display outlines carry one.
            obstacle.id = index
            entry = Obstacle(
                id=index,
                name=fixture.name,
                boundary=sample_inflated_outline(obstacle, inflation_radius=0.0),
                center=(obstacle.center.x, obstacle.center.y),
                radius=fixture.radius if isinstance(fixture, Circle) and fixture.draggable else 0.0,
            )
            self.obstacles.append(entry)
            if entry.draggable:
                self.robot = entry

        logger.info(f"seeded {len(self.obstacles)} obstacles on the {table_enum.name.lower()} table")

    def _append(self, fixture: Fixture) -> int:
        """Append one fixture through the factory that matches its shape."""
        match fixture:
            case Circle():
                return self.shared_obstacles.append_circle(fixture.x, fixture.y, fixture.radius)
            case Rectangle():
                return self.shared_obstacles.append_rectangle(
                    fixture.x, fixture.y, fixture.angle, fixture.length_x, fixture.length_y
                )
            case _:
                raise TypeError(f"unsupported fixture {type(fixture).__name__}")

    def move_robot(self, x: float, y: float) -> None:
        """Move the dragged obstacle.

        Goes through ``set_center()`` rather than writing the outline: the obstacle is displaced as
        a rigid body, which for a disc is its single outline point. Writing the centre alone would
        leave the outline where it was, and the graph would keep routing around an obstacle that is
        no longer there.
        """
        if self.robot is None:
            return

        self.shared_obstacles[self.robot.id].set_center(x, y, 0.0)
        self.robot.center = (x, y)
        self.robot.boundary = sample_inflated_outline(self.shared_obstacles[self.robot.id], inflation_radius=0.0)

    def rebuild(self, corner_count: int, inflation_radius: float, clearance: float) -> GraphSnapshot:
        """Publish the parameters, rebuild the graph, and return views of the result."""
        margin = self.table_margin

        self.graph_lock.start_writing()
        try:
            self.shared_params.corner_count = corner_count
            self.shared_params.inflation_radius = inflation_radius
            self.shared_params.clearance = clearance

            start = perf_counter()
            self.graph.build(
                self.table.x_min + margin,
                self.table.y_min + margin,
                self.table.x_max - margin,
                self.table.y_max - margin,
            )
            build_time = perf_counter() - start
        finally:
            self.graph_lock.finish_writing()

        snapshot = GraphSnapshot(
            nodes=self.graph.get_nodes(),
            edges=self.graph.get_edges(),
            hulls=[self.graph.get_hull(i) for i in range(self.graph.hull_count)],
            rings=[
                np.array(sample_nodes(self.shared_obstacles[obstacle.id], self.shared_params))
                for obstacle in self.obstacles
            ],
            effective_limits=self.graph.effective_limits,
            build_time=build_time,
            nodes_truncated=self.graph.nodes_truncated,
            edges_truncated=self.graph.edges_truncated,
        )

        logger.debug(
            f"build: N={corner_count} rho={inflation_radius} clearance={clearance} "
            f"-> {len(snapshot.nodes)} nodes, {len(snapshot.edges)} edges "
            f"in {build_time * 1000:.1f} ms"
        )
        return snapshot

    def close(self) -> None:
        """Release every handle, in reverse order of acquisition.

        These are nanobind wrappers over the segment, not Python objects that can be collected in
        any order: each one has to go before the segment it points into.
        """
        self.graph = None
        self.graph_lock = None
        self.shared_params = None
        self.shared_obstacles = None
        self.shared_table_limits = None
        self.shared_properties = None
        self.shared_memory = None

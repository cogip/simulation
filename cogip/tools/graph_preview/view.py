"""The 2D view: raw obstacle, its inflation, and the graph built over it.

Everything drawn here arrives as a polyline or a point array from the C++ side. The view owns no
geometry of its own, which is the point: what it shows is what the planner sees, not a second
rendering of the same formulas.
"""

import math

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from cogip.tools.planner.table import Table
from .shared_memory import GraphSnapshot, Obstacle

#: Inner margin around the table, device pixels.
VIEW_MARGIN = 28

#: Drawn thickness of a table wall, mm. Cosmetic: the wall stops the robot by being a limit, not
#: by having a thickness.
WALL_THICKNESS = 22.0

#: Radius of a node marker, device pixels. Fixed rather than in millimetres, so zooming does not
#: turn the nodes into discs that could be mistaken for obstacles.
NODE_RADIUS = 2.6

BACKGROUND = QtGui.QColor("#1B1B1D")
TABLE_FILL = QtGui.QColor("#232326")
TABLE_BORDER = QtGui.QColor("#6E6E78")
WALL_FILL = QtGui.QColor("#3A3A40")
OBSTACLE_FILL = QtGui.QColor("#8E8E96")
OBSTACLE_LINE = QtGui.QColor("#B4B4BE")

# The inflation is a field, not a line: it wants to be legible under the graph rather than compete
# with it. Violet keeps it clear of both the blue of the edges and the orange of the robot, which
# is the only reason it is not simply a lighter grey.
INFLATION_FILL = QtGui.QColor(148, 103, 189, 46)
INFLATION_LINE = QtGui.QColor(198, 164, 232, 235)

# Deliberately faint. A full table produces thousands of edges, and at any strength that makes a
# single edge crisp they stack into one opaque mass where the graph is dense — which is where one
# actually wants to see through it. Faint enough to overlap readably, so density itself reads.
EDGE_LINE = QtGui.QColor(90, 170, 235, 38)

RING_LINE = QtGui.QColor(120, 220, 120, 130)
NODE_FILL = QtGui.QColor("#5CD65C")
NODE_LINE = QtGui.QColor("#12300F")
ROBOT_FILL = QtGui.QColor("#E95420")
ROBOT_LINE = QtGui.QColor("#FF9166")


class GraphView(QtWidgets.QWidget):
    """Draws the table, the obstacles and the graph, in that order of increasing interest.

    One obstacle is draggable, standing for a robot. Moving it is the point of the window: a graph
    is easy to believe when it is still, and the parameters that matter show themselves in how it
    reorganises around something that moves.
    """

    robot_moved = QtCore.Signal(float, float)
    """The dragged obstacle wants to be at these table coordinates, mm."""

    def __init__(self, table: Table, obstacles: list[Obstacle], parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._table = table
        self._obstacles = obstacles
        self._snapshot: GraphSnapshot | None = None
        self._dragging = False

        # The scene is expensive to rasterise and changes only when the graph does, so it is drawn
        # into a pixmap and blitted. Without this, every cursor move over the widget repays the
        # whole cost — and the cursor moves a lot, since hovering is how one finds the robot.
        self._cache: QtGui.QPixmap | None = None

        # World to device, recomputed on resize: uniform scale, Y pointing up.
        self._scale = 1.0
        self._origin = (0.0, 0.0)
        self._clip = QtCore.QRectF()

        self.setMinimumSize(960, 700)
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)

    def set_snapshot(self, snapshot: GraphSnapshot) -> None:
        """Adopt a new build and repaint.

        The arrays inside are views of shared memory, so they are consumed here and never kept
        across a rebuild.
        """
        self._snapshot = snapshot
        self._cache = None
        self.update()

    def clear(self) -> None:
        """Drop the arrays borrowed from shared memory.

        Called before the segment is released: these are views into it, not copies, so keeping one
        past the unmap would read memory that is no longer there.
        """
        self._snapshot = None
        self._cache = None

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        self._fit()
        self._cache = None

    def _fit(self) -> None:
        """Fit the table in the widget, aspect ratio locked.

        The table is 2000 mm along X and 3000 along Y, so laying X out horizontally would stand it
        on end. Turned a quarter turn counter-clockwise it lies the way everyone looks at it, and
        the way the monitor shows it: the long axis across the window.
        """
        across = self._table.y_max - self._table.y_min
        down = self._table.x_max - self._table.x_min

        available_w = max(self.width() - 2 * VIEW_MARGIN, 1)
        available_h = max(self.height() - 2 * VIEW_MARGIN, 1)
        self._scale = min(available_w / across, available_h / down)

        # Centre what is left over, so the table sits in the middle whatever the window shape.
        center_x = (self._table.x_min + self._table.x_max) / 2
        center_y = (self._table.y_min + self._table.y_max) / 2
        self._origin = (
            self.width() / 2 + center_y * self._scale,
            self.height() / 2 + center_x * self._scale,
        )

        # Inflation and rings both extend past an obstacle, so an obstacle against a wall throws
        # them outside the table. Cut them at the walls: the margin around the table is framing,
        # and geometry loose in it reads as a drawing that overflowed rather than as an obstacle
        # that touches the edge.
        wall = WALL_THICKNESS * self._scale
        self._clip = self._rect((self._table.x_min, self._table.y_min, self._table.x_max, self._table.y_max)).adjusted(
            -wall, -wall, wall, wall
        )

    def _to_device(self, points: np.ndarray) -> np.ndarray:
        """Map an (n, 2) array of millimetres to device pixels.

        A quarter turn counter-clockwise, which is the composition of the axis swap and the Y flip
        the widget needs anyway: table +Y runs left across the window, table +X runs up it.
        """
        out = np.empty_like(points, dtype=np.float64)
        out[:, 0] = self._origin[0] - points[:, 1] * self._scale
        out[:, 1] = self._origin[1] - points[:, 0] * self._scale
        return out

    def _to_world(self, x: float, y: float) -> tuple[float, float]:
        """Map a device position back to millimetres."""
        return (self._origin[1] - y) / self._scale, (self._origin[0] - x) / self._scale

    def _robot(self) -> Obstacle | None:
        return next((obstacle for obstacle in self._obstacles if obstacle.draggable), None)

    def _grabs(self, event: QtGui.QMouseEvent) -> bool:
        """Whether a press at this position lands on the draggable obstacle."""
        robot = self._robot()
        if robot is None:
            return False
        x, y = self._to_world(event.position().x(), event.position().y())
        return math.hypot(x - robot.center[0], y - robot.center[1]) <= robot.radius

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802 (Qt override)
        if event.button() == QtCore.Qt.MouseButton.LeftButton and self._grabs(event):
            self._dragging = True
            # The edges are the expensive layer and the least useful mid-drag: what one watches is
            # the obstacle field and the rings reorganising. They come back on release.
            self._cache = None
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802 (Qt override)
        if not self._dragging:
            # Say so before the click: a shape that can be grabbed should look like it.
            shape = QtCore.Qt.CursorShape.OpenHandCursor if self._grabs(event) else QtCore.Qt.CursorShape.ArrowCursor
            self.setCursor(shape)
            super().mouseMoveEvent(event)
            return

        self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
        x, y = self._to_world(event.position().x(), event.position().y())

        # Held inside the table: a node outside it is discarded, so an obstacle dragged out would
        # simply stop having any effect, which looks like the drag broke.
        x = min(max(x, self._table.x_min), self._table.x_max)
        y = min(max(y, self._table.y_min), self._table.y_max)
        self.robot_moved.emit(x, y)
        event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:  # noqa: N802 (Qt override)
        if self._dragging and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._dragging = False
            self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
            self._cache = None
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    @staticmethod
    def _polygon(device_points: np.ndarray) -> QtGui.QPolygonF:
        return QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in device_points])

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: N802 (Qt override)
        if self._cache is None:
            self._cache = self._render_scene()
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self._cache)
        painter.end()

    @property
    def edges_deferred(self) -> bool:
        """Whether the last scene left the edges out."""
        return self._dragging

    def _render_scene(self) -> QtGui.QPixmap:
        """Rasterise the whole scene once, at device resolution."""
        ratio = self.devicePixelRatio()
        pixmap = QtGui.QPixmap(int(self.width() * ratio), int(self.height() * ratio))
        pixmap.setDevicePixelRatio(ratio)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), BACKGROUND)

        self._draw_table(painter)
        painter.setClipRect(self._clip)

        # The inflated shapes go under the raw ones so both stay readable where they differ, and
        # the graph goes over everything: an edge that crosses an obstacle is the one thing this
        # window exists to catch, so nothing may hide it.
        if self._snapshot is not None:
            self._draw_inflation(painter, fill_only=True)
        self._draw_obstacles(painter)
        if self._snapshot is not None:
            self._draw_inflation(painter, fill_only=False)
            self._draw_wall_inflation(painter)
            self._draw_rings(painter)
            if not self._dragging:
                self._draw_edges(painter)
            self._draw_nodes(painter)

        painter.end()
        return pixmap

    def _rect(self, box: tuple[float, float, float, float]) -> QtCore.QRectF:
        """Map a (min_x, min_y, max_x, max_y) box in millimetres to a device rectangle."""
        corners = self._to_device(np.array([[box[0], box[1]], [box[2], box[3]]]))
        return QtCore.QRectF(
            QtCore.QPointF(corners[0][0], corners[0][1]),
            QtCore.QPointF(corners[1][0], corners[1][1]),
        ).normalized()

    def _draw_table(self, painter: QtGui.QPainter) -> None:
        """The playing surface, and the walls around it.

        The walls are drawn as walls rather than implied by the edge of the widget, because they
        are an obstacle like any other: what stops the robot is not the end of the drawing.
        """
        table = self._rect((self._table.x_min, self._table.y_min, self._table.x_max, self._table.y_max))
        wall = WALL_THICKNESS * self._scale

        painter.setBrush(WALL_FILL)
        painter.setPen(QtGui.QPen(TABLE_BORDER, 1.5))
        painter.drawRect(table.adjusted(-wall, -wall, wall, wall))

        painter.setBrush(TABLE_FILL)
        painter.setPen(QtGui.QPen(TABLE_BORDER, 1))
        painter.drawRect(table)

    def _draw_wall_inflation(self, painter: QtGui.QPainter) -> None:
        """The boundary the grown walls leave behind.

        Growing a wall shrinks the region rather than adding a shape, so this is the one piece of
        inflation with no hull of its own — and without it the graph looks as though it simply
        chose to keep away from the edges.
        """
        assert self._snapshot is not None
        box = self._snapshot.effective_limits
        if box[0] >= box[2] or box[1] >= box[3]:
            return

        pen = QtGui.QPen(INFLATION_LINE, 1.2)
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.setPen(pen)
        painter.drawRect(self._rect(box))

    def _draw_obstacles(self, painter: QtGui.QPainter) -> None:
        for obstacle in self._obstacles:
            if not obstacle.boundary:
                continue
            draggable = obstacle.draggable
            painter.setBrush(ROBOT_FILL if draggable else OBSTACLE_FILL)
            painter.setPen(QtGui.QPen(ROBOT_LINE if draggable else OBSTACLE_LINE, 1.2))
            painter.drawPolygon(self._polygon(self._to_device(np.asarray(obstacle.boundary))))

    def _draw_inflation(self, painter: QtGui.QPainter, *, fill_only: bool) -> None:
        assert self._snapshot is not None

        polygons = [self._polygon(self._to_device(hull)) for hull in self._snapshot.hulls if len(hull) > 0]
        if not polygons:
            return

        if fill_only:
            # Filled as one path rather than one polygon at a time. What the fill stands for is the
            # region a node cannot be in, and that region is the *union* of the inflated shapes: a
            # translucent brush applied per obstacle would instead darken wherever two overlap,
            # reading as a gradient of forbiddenness that does not exist. On a full table most of
            # them overlap, so this is the difference between a picture and a smear.
            path = QtGui.QPainterPath()
            path.setFillRule(QtCore.Qt.FillRule.WindingFill)
            for polygon in polygons:
                path.addPolygon(polygon)
            painter.setBrush(INFLATION_FILL)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawPath(path)
            return

        pen = QtGui.QPen(INFLATION_LINE, 1.2)
        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.setPen(pen)
        for polygon in polygons:
            painter.drawPolygon(polygon)

    def _draw_rings(self, painter: QtGui.QPainter) -> None:
        """The circumscribed ring of each obstacle, closed.

        Drawn as a polygon, not as the loose dots the nodes would otherwise be, because this is the
        one shape in the window that the corner count changes: at a low count it is visibly a
        coarse polygon standing well clear of the dashed boundary, and it tightens onto it as the
        count rises. Its chords are what the edges of the graph have to be able to follow.
        """
        assert self._snapshot is not None

        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.setPen(QtGui.QPen(RING_LINE, 1.1))
        for ring in self._snapshot.rings:
            if len(ring) < 2:
                continue
            painter.drawPolygon(self._polygon(self._to_device(ring)))

    def _draw_edges(self, painter: QtGui.QPainter) -> None:
        assert self._snapshot is not None
        nodes, edges = self._snapshot.nodes, self._snapshot.edges
        if len(edges) == 0:
            return

        # Antialiasing off for this layer alone. What the edges cost is rasterisation, not the
        # Python call — measured at roughly 40 % more per edge with it on, against 4 % for building
        # the list — and it buys nothing here: what one reads from a few thousand overlapping
        # translucent lines is their density, which a smoothed end on each does not affect.
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, False)

        # One drawLines() over the whole graph rather than a call per edge. The edge count grows as
        # the square of the node count, so a full table at a fine corner count reaches tens of
        # thousands; that is why this layer is skipped during a drag and the scene is cached.
        device = self._to_device(nodes)
        segments = device[np.asarray(edges, dtype=np.intp)]
        painter.setPen(QtGui.QPen(EDGE_LINE, 1))
        painter.drawLines([QtCore.QLineF(a[0], a[1], b[0], b[1]) for a, b in segments])

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

    def _draw_nodes(self, painter: QtGui.QPainter) -> None:
        assert self._snapshot is not None
        if len(self._snapshot.nodes) == 0:
            return

        # A dark rim, because where the graph is dense a node otherwise dissolves into its own
        # edges — and the nodes are what one is checking the position of.
        painter.setBrush(NODE_FILL)
        painter.setPen(QtGui.QPen(NODE_LINE, 1))
        for x, y in self._to_device(self._snapshot.nodes):
            painter.drawEllipse(QtCore.QPointF(x, y), NODE_RADIUS, NODE_RADIUS)

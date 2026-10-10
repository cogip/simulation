"""The window: the view, the three parameters that shape the graph, and what the build reported."""

from PySide6 import QtCore, QtGui, QtWidgets

from cogip.cpp.libraries.graph import GRAPH_CORNER_COUNT_MAX
from .shared_memory import GraphPreviewMemory
from .view import (
    EDGE_LINE,
    INFLATION_LINE,
    OBSTACLE_FILL,
    RING_LINE,
    ROBOT_FILL,
    GraphView,
)

#: Delay between the last slider move and the rebuild it triggers, milliseconds.
#:
#: A build is a few milliseconds, but dragging a slider emits a value per pixel crossed. Coalescing
#: them keeps the drag smooth without making the result lag behind the handle.
REBUILD_DEBOUNCE_MS = 50

#: Bounds of the two radii, millimetres.
INFLATION_MAX = 500
CLEARANCE_MIN = 1
CLEARANCE_MAX = 100


class ParameterRow(QtWidgets.QWidget):
    """A slider and a spin box showing the same integer, with a label and a unit."""

    value_changed = QtCore.Signal(int)

    def __init__(self, label: str, minimum: int, maximum: int, value: int, suffix: str, tip: str):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)

        caption = QtWidgets.QLabel(label)
        caption.setToolTip(tip)
        layout.addWidget(caption)

        row = QtWidgets.QHBoxLayout()
        self._slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._slider.setRange(minimum, maximum)
        self._slider.setValue(value)
        self._spin = QtWidgets.QSpinBox()
        self._spin.setRange(minimum, maximum)
        self._spin.setValue(value)
        self._spin.setSuffix(suffix)
        row.addWidget(self._slider, 1)
        row.addWidget(self._spin)
        layout.addLayout(row)

        # Kept in step without a loop: setValue on an unchanged value emits nothing.
        self._slider.valueChanged.connect(self._spin.setValue)
        self._spin.valueChanged.connect(self._slider.setValue)
        self._spin.valueChanged.connect(self.value_changed)

    def value(self) -> int:
        return self._spin.value()


class GraphPreviewWindow(QtWidgets.QMainWindow):
    """Drives one rebuild per parameter change and shows what came back."""

    def __init__(self, memory: GraphPreviewMemory, corner_count: int, inflation_radius: float, clearance: float):
        super().__init__()
        self._memory = memory

        self.setWindowTitle("COGIP graph preview")

        self._view = GraphView(memory.table, memory.obstacles)
        self._view.robot_moved.connect(self._move_robot)

        self._corners = ParameterRow(
            "Corner samples (N)",
            1,
            GRAPH_CORNER_COUNT_MAX,
            corner_count,
            "",
            "Sample points per rounded corner. This moves the green ring, not the dashed outline: "
            "the outline is the exact inflated shape and does not depend on it, while the ring is "
            "the approximation the graph is built on. A low N pushes the ring well clear of the "
            "outline; raising it tightens the ring onto it.",
        )
        self._inflation = ParameterRow(
            "Inflation radius (rho)",
            0,
            INFLATION_MAX,
            round(inflation_radius),
            " mm",
            "The robot, shrunk to a point. Added to the corner radius of every obstacle, which is "
            "the whole of the inflation: one addition, no outline offset.",
        )
        self._clearance = ParameterRow(
            "Clearance",
            CLEARANCE_MIN,
            CLEARANCE_MAX,
            max(round(clearance), CLEARANCE_MIN),
            " mm",
            "Distance every node keeps from the inflated shape. Cannot be zero: a node on the "
            "boundary counts as inside it, and every edge leaving it would be rejected.",
        )

        panel = QtWidgets.QWidget()
        panel.setFixedWidth(300)
        panel_layout = QtWidgets.QVBoxLayout(panel)
        panel_layout.addWidget(self._corners)
        panel_layout.addWidget(self._inflation)
        panel_layout.addWidget(self._clearance)
        panel_layout.addWidget(self._legend())
        panel_layout.addStretch(1)

        central = QtWidgets.QWidget()
        central_layout = QtWidgets.QHBoxLayout(central)
        central_layout.addWidget(self._view, 1)
        central_layout.addWidget(panel)
        self.setCentralWidget(central)

        self._status = QtWidgets.QLabel()
        self.statusBar().addWidget(self._status)

        self._debounce = QtCore.QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(REBUILD_DEBOUNCE_MS)
        self._debounce.timeout.connect(self._rebuild)

        for row in (self._corners, self._inflation, self._clearance):
            row.value_changed.connect(lambda _: self._debounce.start())

        self._rebuild()

    def _legend(self) -> QtWidgets.QWidget:
        """Name the four things on screen, so the colours mean something."""
        box = QtWidgets.QGroupBox("Legend")
        layout = QtWidgets.QVBoxLayout(box)
        entries = [
            (OBSTACLE_FILL, "Obstacle, exact shape"),
            (ROBOT_FILL, "Robot — drag it"),
            (INFLATION_LINE, "Inflated boundary, exact"),
            (RING_LINE, "Node ring, follows N"),
            (EDGE_LINE, "Graph edge"),
        ]
        for color, text in entries:
            row = QtWidgets.QHBoxLayout()
            swatch = QtWidgets.QLabel()
            swatch.setFixedSize(14, 14)
            swatch.setAutoFillBackground(True)
            palette = swatch.palette()
            palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(color.rgb()))
            swatch.setPalette(palette)
            row.addWidget(swatch)
            row.addWidget(QtWidgets.QLabel(text), 1)
            layout.addLayout(row)
        return box

    def _move_robot(self, x: float, y: float) -> None:
        """Follow the mouse, then rebuild through the same debounce as the sliders.

        A drag emits a position per pixel crossed, and each one would otherwise queue a build. The
        obstacle moves at mouse rate; the graph catches up at build rate.
        """
        self._memory.move_robot(x, y)
        self._debounce.start()

    def _rebuild(self) -> None:
        snapshot = self._memory.rebuild(
            corner_count=self._corners.value(),
            inflation_radius=float(self._inflation.value()),
            clearance=float(self._clearance.value()),
        )
        self._view.set_snapshot(snapshot)

        message = (
            f"{len(snapshot.nodes)} nodes, {len(snapshot.edges)} edges, built in {snapshot.build_time * 1000:.1f} ms"
        )
        if snapshot.nodes_truncated:
            message += "  —  NODE CAPACITY REACHED, graph incomplete"
        if snapshot.edges_truncated:
            message += "  —  EDGE CAPACITY REACHED, graph incomplete"
        if self._view.edges_deferred:
            message += "  —  edges hidden while dragging"
        self._status.setText(message)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802 (Qt override)
        # The view holds numpy views of the segment, so it has to let go before the segment does.
        self._debounce.stop()
        self._view.clear()
        self._memory.close()
        super().closeEvent(event)

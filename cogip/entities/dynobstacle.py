from typing import List, Tuple

from PySide6 import QtCore, QtGui
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras

from cogip.models import models
from .path import PathEntity


class DynBaseObstacleEntity(Qt3DCore.QEntity):
    """
    A dynamic obstacle detected by the robot.

    Base class for rectangle and circle obstacles.
    """

    def __init__(self, parent: Qt3DCore.QEntity):
        """
        Class constructor.
        """
        super().__init__(parent)
        self.parent = parent
        self.points = []

        self.material = Qt3DExtras.QDiffuseSpecularMaterial(self)
        self.material.setDiffuse(QtGui.QColor.fromRgb(255, 0, 0, 100))
        self.material.setDiffuse(QtGui.QColor.fromRgb(255, 0, 0, 100))
        self.material.setSpecular(QtGui.QColor.fromRgb(255, 0, 0, 100))
        self.material.setShininess(1.0)
        self.material.setAlphaBlendingEnabled(True)
        self.addComponent(self.material)

        self.transform = Qt3DCore.QTransform(self)
        self.addComponent(self.transform)

        self.bb = PathEntity(QtCore.Qt.darkRed, self.parent)

    def set_bounding_box(self, points: List[models.Vertex]) -> None:
        """
        """
        if self.points == points:
            return

        self.points = points
        bb_points = []
        if points:
            for point in points:
                bb_points.append(models.Vertex(x=point.x, y=point.y, z=5))
            bb_points.append(models.Vertex(x=points[0].x, y=points[0].y, z=5))
        self.bb.set_points(bb_points)

    def setEnabled(self, isEnabled: bool) -> None:
        super().setEnabled(isEnabled)
        self.bb.setEnabled(isEnabled)


class DynRectObstacleEntity(DynBaseObstacleEntity):
    """
    A dynamic rectangle obstacle detected by the robot.

    Represented as a transparent red cube.
    """

    def __init__(self, parent: Qt3DCore.QEntity):
        """
        Class constructor.
        """
        super().__init__(parent)
        self.size: Tuple[int, int] = None
        self.position: Tuple[int, int, int] = None

        self.mesh = Qt3DExtras.QCuboidMesh()
        self.mesh.setZExtent(200)
        self.addComponent(self.mesh)

    def set_size(self, length: int, width: int) -> None:
        """
        Set the size of the dynamic obstacle.

        Arguments:
            length: Length
            width: Width
        """
        if self.size == (length, width):
            return

        self.size = (length, width)

        self.mesh.setXExtent(width)
        self.mesh.setYExtent(length)

    def set_position(self, x: int, y: int, rotation: int) -> None:
        """
        Set the position and orientation of the dynamic obstacle.

        Arguments:
            x: X position
            y: Y position
            rotation: Rotation
        """
        if self.position == (x, y, rotation):
            return

        self.position = (x, y, rotation)

        self.transform.setTranslation(QtGui.QVector3D(x, y, self.mesh.zExtent() / 2))
        self.transform.setRotationZ(rotation)


class DynCircleObstacleEntity(DynBaseObstacleEntity):
    """
    A dynamic circle obstacle detected by the robot.

    Represented as a transparent red cylinder.
    """

    def __init__(self, parent: Qt3DCore.QEntity):
        """
        Class constructor.
        """
        super().__init__(parent)
        self.position: Tuple[int, int, int] = None

        self.mesh = Qt3DExtras.QCylinderMesh()
        self.mesh.setLength(200)
        self.mesh.setRadius(400)
        self.addComponent(self.mesh)

        self.transform.setRotationX(90)

    def set_position(self, x: int, y: int, radius: int) -> None:
        """
        Set the position and size of the dynamic obstacle.

        Arguments:
            x: Center X position
            y: Center Y position
            radius: Obstacle radius
        """
        if self.position == (x, y, radius):
            return
        self.position = (x, y, radius)

        self.transform.setTranslation(QtGui.QVector3D(x, y, self.mesh.length() / 2))
        self.mesh.setRadius(radius)

from PySide2 import QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DExtras import Qt3DExtras


class DynObstacleEntity(Qt3DCore.QEntity):
    """
    A dynamic obstacle detected by the robot.

    Represented as a transparent red cube.
    """

    def __init__(self):
        """
        Class constructor.
        """
        super(DynObstacleEntity, self).__init__()

        self.mesh = Qt3DExtras.QCuboidMesh()
        self.mesh.setZExtent(600)
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QDiffuseSpecularMaterial(self)
        self.material.setDiffuse(QtGui.QColor.fromRgb(255, 0, 0, 100))
        self.material.setDiffuse(QtGui.QColor.fromRgb(255, 0, 0, 100))
        self.material.setSpecular(QtGui.QColor.fromRgb(255, 0, 0, 100))
        self.material.setShininess(1.0)
        self.material.setAlphaBlendingEnabled(True)
        self.addComponent(self.material)

        self.transform = Qt3DCore.QTransform(self)
        self.addComponent(self.transform)

    def set_position(self, x: int, y: int, rotation: int) -> None:
        """
        Set the position and orientation of the dynamic obstacle.

        Arguments:
            x: X position
            y: Y position
            rotation: Rotation
        """
        self.transform.setTranslation(QtGui.QVector3D(x, y, self.mesh.zExtent()/2))
        self.transform.setRotationZ(rotation)

    def set_size(self, length: int, width: int) -> None:
        """
        Set the size of the dynamic obstacle.

        Arguments:
            length: Length
            width: Width
        """
        self.mesh.setXExtent(width)
        self.mesh.setYExtent(length)

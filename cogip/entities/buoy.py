from pathlib import Path

from PySide2 import QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DExtras import Qt3DExtras

from cogip import logger
from cogip.entities.asset import AssetEntity


class BuoyEntity(AssetEntity):
    """
    The buoy entity displayed on the table.

    Attributes:
        asset_path: Path of the asset file
        asset_name: Interval in seconds between each sensors update
        asset_scale: Scale to apply to the entity after load
    """

    asset_path: Path = Path("assets/buoy.dae")
    asset_name: str = "myscene"
    asset_scale: float = 1000.0
    default_color = QtGui.QColor(QtCore.Qt.blue)
    green = QtGui.QColor(QtCore.Qt.darkGreen)
    red = QtGui.QColor(QtCore.Qt.red)

    def __init__(self, x: float, y: float, color: str = "green"):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].

        Arguments:
            x: X position
            y: Y position
            color: The color of the robot
        """
        super().__init__(self.asset_path, scale=self.asset_scale)
        self.x = x
        self.y = y
        self.color = getattr(self, color, self.default_color)

    def post_init(self):
        """
        Function called once the asset has been loaded.

        Set color and position.
        """
        super().post_init()

        self.asset_entity = self.findChild(Qt3DCore.QEntity, self.asset_name)
        if not self.asset_entity:
            logger.error(f"Entity '{self.asset_name}' not found in {self.asset_path}")
            return

        self.asset_entity.setParent(self)

        if self.scale != 1:
            for comp in self.asset_entity.components():
                if isinstance(comp, Qt3DCore.QTransform):
                    comp.setScale(self.scale)
                    break

        for material in self.asset_entity.findChildren(Qt3DExtras.QPhongMaterial):
            material.setDiffuse(self.color)
            material.setSpecular(self.color)

        self.transform_component.setTranslation(
            QtGui.QVector3D(self.x, self.y, 115))
        self.transform_component.setRotationX(90)

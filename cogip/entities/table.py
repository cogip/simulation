from pathlib import Path
from typing import Optional

from PySide2 import QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DExtras import Qt3DExtras

from cogip import logger
from cogip.entities.asset import AssetEntity


buoys_colors = {
    "green": QtGui.QColor(QtCore.Qt.darkGreen),
    "red": QtGui.QColor(QtCore.Qt.red)
}

buoys = [
    # Blue side (+X)
    {"x": 1500-300, "y": 400, "color": buoys_colors["red"]},
    {"x": 1500-300, "y": 1200, "color": buoys_colors["green"]},
    {"x": 1500-445, "y": 515, "color": buoys_colors["green"]},
    {"x": 1500-445, "y": 1085, "color": buoys_colors["red"]},
    {"x": 1500-670, "y": 100, "color": buoys_colors["red"]},
    {"x": 1500-956, "y": 400, "color": buoys_colors["green"]},
    {"x": 1500-1005, "y": 1955, "color": buoys_colors["red"]},
    {"x": 1500-1065, "y": 1655, "color": buoys_colors["green"]},
    {"x": 1500-1100, "y": 800, "color": buoys_colors["red"]},
    {"x": 1500-1270, "y": 1200, "color": buoys_colors["green"]},
    {"x": 1500-1335, "y": 1655, "color": buoys_colors["red"]},
    {"x": 1500-1395, "y": 1955, "color": buoys_colors["green"]},
    # Yellow side (-X)
    {"x": 1500-1605, "y": 1955, "color": buoys_colors["red"]},
    {"x": 1500-1665, "y": 1655, "color": buoys_colors["green"]},
    {"x": 1500-1730, "y": 1200, "color": buoys_colors["red"]},
    {"x": 1500-1900, "y": 800, "color": buoys_colors["green"]},
    {"x": 1500-1935, "y": 1655, "color": buoys_colors["red"]},
    {"x": 1500-1995, "y": 1955, "color": buoys_colors["green"]},
    {"x": 1500-2044, "y": 400, "color": buoys_colors["red"]},
    {"x": 1500-2330, "y": 100, "color": buoys_colors["green"]},
    {"x": 1500-2555, "y": 515, "color": buoys_colors["red"]},
    {"x": 1500-2555, "y": 1085, "color": buoys_colors["green"]},
    {"x": 1500-2700, "y": 400, "color": buoys_colors["green"]},
    {"x": 1500-2700, "y": 1200, "color": buoys_colors["red"]},
    # Shoal area (floating buoys)
    {"x": 1500-1200, "y": 75, "color": buoys_colors["green"]},
    {"x": 1500-1340, "y": 330, "color": buoys_colors["green"]},
    {"x": 1500-1360, "y": 125, "color": buoys_colors["red"]},
    {"x": 1500-1660, "y": 400, "color": buoys_colors["red"]},
    {"x": 1500-1700, "y": 100, "color": buoys_colors["red"]},
    {"x": 1500-1900, "y": 200, "color": buoys_colors["green"]}
]


class TableEntity(AssetEntity):
    """
    The table entity.

    Attributes:
        asset_path: Path of the asset file
        asset_name: Interval in seconds between each sensors update
        asset_scale: Scale to apply to the entity after load
        ground_entity_name: name of the ground entity
    """

    asset_path: Path = Path("assets/table2021.dae")
    asset_name: str = "myscene"
    asset_scale: float = 1000.0
    ground_entity_name = "node18"

    def __init__(self, parent: Optional[Qt3DCore.QEntity] = None):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].
        """
        super().__init__(self.asset_path, scale=self.asset_scale, parent=parent)
        self.buoy_entities = []

    def post_init(self):
        """
        Function called once the asset has been loaded.
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

        # Find the ground entity and remove its material
        self.ground_entity = self.findChild(Qt3DCore.QEntity, self.ground_entity_name)
        if not self.ground_entity:
            logger.warning(f"Entity '{self.ground_entity_name}' not found in {self.asset_path}")
        else:
            for comp in self.ground_entity.components():
                if isinstance(comp, Qt3DExtras.QPhongMaterial):
                    self.ground_entity.removeComponent(comp)
                    break

        for buoy in buoys:
            entity = Qt3DCore.QEntity(self)
            self.buoy_entities.append(entity)

            mesh = Qt3DExtras.QConeMesh(entity)
            mesh.setBottomRadius(72/2)
            mesh.setTopRadius(54/2)
            mesh.setLength(115)
            mesh.setHasTopEndcap(True)
            entity.addComponent(mesh)

            material = Qt3DExtras.QPhongMaterial(entity)
            material.setDiffuse(QtGui.QColor(buoy["color"]))
            entity.addComponent(material)

            transform = Qt3DCore.QTransform(entity)
            transform.setTranslation(QtGui.QVector3D(buoy["x"], buoy["y"], 115.0/2))
            transform.setRotationX(90)
            entity.addComponent(transform)

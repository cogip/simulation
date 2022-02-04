from pathlib import Path
from typing import Optional

from PySide6 import QtGui
from PySide6.Qt3DCore import Qt3DCore

from cogip import logger
from cogip.entities.asset import AssetEntity


class TableEntity(AssetEntity):
    """
    The table entity.

    Attributes:
        asset_path: Path of the asset file
        asset_name: Interval in seconds between each sensors update
        asset_scale: Scale to apply to the entity after load
        ground_entity_name: name of the ground entity
    """
    asset_path: Path = Path("assets/table2022-without-samples.dae")
    asset_name: str = "myscene"
    ground_entity_name = "node5"

    def __init__(self, parent: Optional[Qt3DCore.QEntity] = None):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].
        """
        super().__init__(self.asset_path, parent=parent)
        self._parent = parent

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
        self.transform_component.setTranslation(QtGui.QVector3D(1500, 0, 0))

        for comp in self.asset_entity.components():
            if isinstance(comp, Qt3DCore.QTransform):
                comp.setRotationX(0)
                comp.setRotationY(0)
                comp.setRotationZ(180)
                break

        # Find the ground entity and remove its material
        self.ground_entity = self.findChild(Qt3DCore.QEntity, self.ground_entity_name)
        if not self.ground_entity:
            logger.warning(f"Entity '{self.ground_entity_name}' not found in {self.asset_path}")
        else:
            self.ground_entity.setEnabled(False)

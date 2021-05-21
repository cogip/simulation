from pathlib import Path

from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DExtras import Qt3DExtras

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

    asset_path: Path = Path("assets/table2021.dae")
    asset_name: str = "myscene"
    asset_scale: float = 1000.0
    ground_entity_name = "node18"

    def __init__(self):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].
        """
        super().__init__(self.asset_path, scale=self.asset_scale)

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

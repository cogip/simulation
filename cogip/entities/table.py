from pathlib import Path
from typing import Optional

from PySide6.Qt3DCore import Qt3DCore

from cogip.entities.asset import AssetEntity


class TableEntity(AssetEntity):
    """
    The table entity.

    Attributes:
        asset_path: Path of the asset file
    """
    asset_path: Path = Path("assets/table2024.dae")

    def __init__(self, parent: Optional[Qt3DCore.QEntity] = None):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].
        """
        super().__init__(self.asset_path, parent=parent)
        self._parent = parent

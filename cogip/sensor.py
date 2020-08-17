from PySide2 import QtCore, QtGui
from PySide2.Qt3DRender import Qt3DRender
from PySide2.QtCore import Slot as qtSlot

from cogip.assetentity import AssetEntity
from cogip.impactentity import ImpactEntity


class Sensor(QtCore.QObject):

    def __init__(
            self,
            asset_entity: AssetEntity,
            name: str,
            origin_x: int,
            origin_y: int
            ):
        super(Sensor, self).__init__()

        self.asset_entity = asset_entity
        self.name = name
        self.distance = None

        direction_x = 1.0 if origin_x > 0 else -1.0 if origin_x < 0 else 0.0
        direction_y = 1.0 if origin_y > 0 else -1.0 if origin_y < 0 else 0.0

        self.ray_caster = Qt3DRender.QRayCaster()
        self.ray_caster.setEnabled(True)
        self.ray_caster.setLength(0)  # Infinite
        self.ray_caster.setRunMode(Qt3DRender.QAbstractRayCaster.Continuous)
        self.ray_caster.setOrigin(QtGui.QVector3D(float(origin_x), float(origin_y), 60))
        self.ray_caster.setDirection(QtGui.QVector3D(direction_x, direction_y, 0))

        self.asset_entity.asset_entity.addComponent(self.ray_caster)

        # Add impact entity
        self.impact_entity = ImpactEntity()
        self.impact_entity.setParent(self.asset_entity)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.handle_hits)
        self.timer.start(50)

    @qtSlot()
    def handle_hits(self):
        distances = [
            hit
            for hit in self.ray_caster.hits()
            if hit.distance() != 0.0 and hit.entity() != self.impact_entity
        ]
        if len(distances):
            self.hit = min(distances, key=lambda x: x.distance())
            self.impact_entity.setEnabled(True)
            self.impact_entity.transform.setTranslation(self.hit.worldIntersection())
        else:
            self.hit = None
            self.impact_entity.setEnabled(False)

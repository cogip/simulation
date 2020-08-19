from PySide2 import QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.QtCore import Slot as qtSlot

from cogip.assetentity import AssetEntity
from cogip.impactentity import ImpactEntity


class Sensor(QtCore.QObject):

    # Class attribute recording all entities that should be detected
    obstacles = []

    # Class attribute recording all sensors
    # Each added obstacle must be registered in all sensors
    all_sensors = []

    def __init__(
            self,
            asset_entity: AssetEntity,
            name: str,
            origin_x: int,
            origin_y: int,
            origin_z: int,
            direction_x: int,
            direction_y: int,
            direction_z: int,
            impact_radius: float = 50,
            impact_color: QtCore.Qt.GlobalColor = QtCore.Qt.red):
        super(Sensor, self).__init__()

        Sensor.all_sensors.append(self)

        self.asset_entity = asset_entity
        self.name = name
        self.distance = None

        self.ray_caster = Qt3DRender.QRayCaster()
        self.ray_caster.setEnabled(False)  # Start casting only when the first obstacle is registered
        self.ray_caster.setLength(0)  # Infinite
        self.ray_caster.setRunMode(Qt3DRender.QAbstractRayCaster.Continuous)
        # self.ray_caster.setRunMode(Qt3DRender.QAbstractRayCaster.SingleShot)
        self.ray_caster.setFilterMode(Qt3DRender.QAbstractRayCaster.AcceptAnyMatchingLayers)
        self.ray_caster.setOrigin(QtGui.QVector3D(float(origin_x), float(origin_y), float(origin_z)))
        self.ray_caster.setDirection(QtGui.QVector3D(direction_x, direction_y, direction_z))
        self.asset_entity.asset_entity.addComponent(self.ray_caster)

        # Add layers for obstacles already present
        for obstacle in self.obstacles:
            self.add_obstacle_layer(obstacle)

        # Add impact entity
        self.impact_entity = ImpactEntity(radius=impact_radius, color=impact_color)
        self.impact_entity.setParent(self.asset_entity)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.handle_hits)
        self.timer.start(50)

    @qtSlot()
    def handle_hits(self):
        distances = [
            hit
            for hit in self.ray_caster.hits()
            if hit.distance() != 0.0
        ]
        if len(distances):
            self.hit = min(distances, key=lambda x: x.distance())
            self.impact_entity.setEnabled(True)
            self.impact_entity.transform.setTranslation(self.hit.worldIntersection())
        else:
            self.hit = None
            self.impact_entity.setEnabled(False)

    @classmethod
    def add_obstacle(cls, obstacle: Qt3DCore.QEntity):
        cls.obstacles.append(obstacle)
        for sensor in cls.all_sensors:
            sensor.add_obstacle_layer(obstacle)

    # Create a QLayer containing the entity to be detected
    # and add it to the ray caster
    def add_obstacle_layer(self, obstacle: Qt3DCore.QEntity):
        # It may be possible to reuse the same layer
        # if it has arlready been added to the obstacle
        layer = Qt3DRender.QLayer(obstacle)
        layer.setRecursive(True)
        layer.setEnabled(True)
        obstacle.addComponent(layer)
        self.ray_caster.addLayer(layer)
        # Activate if not already done
        self.ray_caster.trigger()


class ToFSensor(Sensor):

    def __init__(
            self,
            asset_entity: AssetEntity,
            name: str,
            origin_x: int,
            origin_y: int):

        super(ToFSensor, self).__init__(
            asset_entity=asset_entity,
            name=name,
            origin_x=origin_x,
            origin_y=origin_y,
            origin_z=60,
            direction_x=origin_x,
            direction_y=origin_y,
            direction_z=0,
            impact_radius=50,
            impact_color=QtCore.Qt.red)


class LidarSensor(Sensor):

    def __init__(
            self,
            asset_entity: AssetEntity,
            name: str,
            origin_x: int,
            origin_y: int,
            direction_x: int,
            direction_y: int):

        super(LidarSensor, self).__init__(
            asset_entity=asset_entity,
            name=name,
            origin_x=origin_x,
            origin_y=origin_y,
            origin_z=400,
            direction_x=direction_x,
            direction_y=direction_y,
            direction_z=0,
            impact_radius=20,
            impact_color=QtCore.Qt.blue)

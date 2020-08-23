import math

import sysv_ipc

from PySide2 import QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DExtras import Qt3DExtras
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

    # Add the obstacle layer to the ray caster
    def add_obstacle_layer(self, obstacle: Qt3DCore.QEntity):
        self.ray_caster.addLayer(obstacle.layer)
        # Activate if not already done
        self.ray_caster.trigger()


class ToFSensor(Sensor):

    shm_key = None
    shm_ptr = None
    shm_data = None
    nb_tof_sensors = 0

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
        self.sensor_id = ToFSensor.nb_tof_sensors
        ToFSensor.nb_tof_sensors += 1
        if ToFSensor.shm_data:
            ToFSensor.shm_data[self.sensor_id] = 65535

        rotation = math.degrees(math.acos((origin_x / math.dist((0, 0), (origin_x, origin_y)))))

        self.entity = Qt3DCore.QEntity()
        self.entity.setParent(self.asset_entity.asset_entity)

        self.mesh = Qt3DExtras.QCuboidMesh()
        self.mesh.setXExtent(10)
        self.mesh.setYExtent(10)
        self.mesh.setZExtent(10)
        self.entity.addComponent(self.mesh)

        self.material = Qt3DExtras.QPhongMaterial()
        self.material.setDiffuse(QtGui.QColor(QtCore.Qt.red))
        self.entity.addComponent(self.material)

        self.transform = Qt3DCore.QTransform()
        self.transform.setTranslation(QtGui.QVector3D(origin_x, origin_y, 60))
        self.transform.setRotationZ(rotation)
        self.entity.addComponent(self.transform)

    @classmethod
    def init_shm(cls):
        cls.shm_ptr = sysv_ipc.SharedMemory(key=None, mode=0o666, flags=sysv_ipc.IPC_CREX, size=1024)
        cls.shm_key = cls.shm_ptr.key
        cls.shm_data = memoryview(cls.shm_ptr).cast('H')

        for i in range(cls.nb_tof_sensors):
            cls.shm_data[i] = 65535

        # cls.shm_ptr.detach()
        # cls.shm_ptr.remove()

    @qtSlot()
    def handle_hits(self):
        super(ToFSensor, self).handle_hits()
        if self.shm_data:
            if self.hit:
                ToFSensor.shm_data[self.sensor_id] = int(self.hit.distance())
            else:
                ToFSensor.shm_data[self.sensor_id] = 65535


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

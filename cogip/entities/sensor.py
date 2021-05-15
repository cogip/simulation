import ctypes
import math
from typing import List, Optional

import sysv_ipc

from PySide2 import QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.QtCore import Slot as qtSlot

from cogip.entities.asset import AssetEntity
from cogip.entities.impact import ImpactEntity

VL53L0X_NUMOF = 6


class ShmData(ctypes.Structure):
    """
    Contains all sensors data shared with the firmware.

    The equivalent C struct is:
    ```c
    struct {
        uint16_t tof[VL53L0X_NUMOF];
        uint16_t lidar[360]
    }
    ```
    """
    _fields_ = [
        ('tof', ctypes.c_ushort * VL53L0X_NUMOF),
        ('lidar', ctypes.c_ushort * 360)
    ]


class Sensor(QtCore.QObject):
    """
    Base class for all sensors.

    The sensors are based on [QRayCaster](https://doc.qt.io/qtforpython-5/PySide2/Qt3DRender/QRayCaster.html).
    It casts a ray and detects collisions with obstacles.
    Detected collision is represented using a [ImpactEntity][cogip.entities.impact.ImpactEntity] object.

    Attributes:
        obstacles: Class attribute recording all entities that should be detected
        all_sensors: Class attribute recording all sensors
        shm_key: Key to the shared memory segment
        shm_ptr: Pointer the shared memory segment
        shm_data: Data class mapped on the shared memory segment
    """
    obstacles: List[Qt3DCore.QEntity] = []
    all_sensors: List["Sensor"] = []

    shm_key: Optional[str] = None
    shm_ptr: Optional[sysv_ipc.SharedMemory] = None
    shm_data: Optional[ShmData] = None

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
        """
        Class constructor.

        Origin and direction are relative to the parent entity (the robot).

        Arguments:
            asset_entity: Entity containing the sensor
            name: Name of the sensor
            origin_x: X origin of the ray caster
            origin_y: Y origin of the ray caster
            origin_z: Z origin of the ray caster
            direction_x: X direction of the ray caster
            direction_y: Y direction of the ray caster
            direction_z: Z direction of the ray caster
            impact_radius: Radius of the `ImpactEntity` representing the collision
            impact_color: Color of the `ImpactEntity` representing the collision
        """
        super(Sensor, self).__init__()

        Sensor.all_sensors.append(self)

        self.origin_x = origin_x
        self.origin_y = origin_y
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

    @qtSlot()
    def update_hit(self):
        """
        Qt Slot

        Compute the distance with the closest detected obstacle.
        """
        distances = [
            hit
            for hit in self.ray_caster.hits()
            if hit.distance() != 0.0
        ]
        self.hit = None
        if len(distances):
            self.hit = min(distances, key=lambda x: x.distance())

    def update_impact(self):
        """
        Display the impact entity at the collision point.
        """
        if self.hit:
            self.impact_entity.setEnabled(True)
            self.impact_entity.transform.setTranslation(self.hit.worldIntersection())
        else:
            self.impact_entity.setEnabled(False)

    @classmethod
    def add_obstacle(cls, obstacle: Qt3DCore.QEntity):
        """
        Class method.

        Register an obstacle added on the table.

        Arguments:
            obstacle: The obstacle to register
        """
        cls.obstacles.append(obstacle)
        for sensor in cls.all_sensors:
            sensor.add_obstacle_layer(obstacle)

    def add_obstacle_layer(self, obstacle: Qt3DCore.QEntity):
        """
        Add the obstacle layer to the ray caster.
        This allows the obstacle to be detected by the ray caster.

        Arguments:
            obstacle: The obstacle to detect
        """
        self.ray_caster.addLayer(obstacle.layer)
        # Activate if not already done
        self.ray_caster.trigger()

    @classmethod
    def init_shm(cls):
        """
        Class method.

        Initialize the shared memory segment used to share
        sensors data with the firmware.
        """
        cls.shm_ptr = sysv_ipc.SharedMemory(key=None, mode=0o666, flags=sysv_ipc.IPC_CREX, size=1024)
        cls.shm_key = cls.shm_ptr.key
        cls.shm_data = ShmData.from_buffer(cls.shm_ptr)

        for i in range(VL53L0X_NUMOF):
            cls.shm_data.tof[i] = 65535

        for i in range(360):
            cls.shm_data.lidar[i] = 65535

        # cls.shm_ptr.detach()
        # cls.shm_ptr.remove()


class ToFSensor(Sensor):
    """
    Specialized ToF sensor.

    It is represented by a small red cube placed at the origin of the ray caster.

    Its impact entity is represented by a small red sphere.
    """
    nb_tof_sensors = 0

    def __init__(
            self,
            asset_entity: AssetEntity,
            name: str,
            origin_x: int,
            origin_y: int):
        """
        Class constructor.

        Arguments:
            asset_entity: Entity containing the sensor
            name: Name of the sensor
            origin_x: X origin of the ray caster
            origin_y: Y origin of the ray caster
        """
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
        self.tof_id = ToFSensor.nb_tof_sensors
        ToFSensor.nb_tof_sensors += 1

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

    @qtSlot()
    def update_hit(self):
        """
        Store the distance of the closest obstacle in the shared memory segment.
        """
        super(ToFSensor, self).update_hit()
        if Sensor.shm_data:
            if self.hit:
                Sensor.shm_data.tof[self.tof_id] = int(self.hit.distance())
            else:
                Sensor.shm_data.tof[self.tof_id] = 65535
        self.update_impact()


class LidarSensor(Sensor):
    """
    Specialized LIDAR sensor.

    Its impact entity is represented by a small blue sphere.
    """

    nb_lidar_sensors = 0

    def __init__(
            self,
            asset_entity: AssetEntity,
            name: str,
            origin_x: int,
            origin_y: int,
            direction_x: int,
            direction_y: int):
        """
        Class constructor.

        Arguments:
            asset_entity: Entity containing the sensor
            name: Name of the sensor
            origin_x: X origin of the ray caster
            origin_y: Y origin of the ray caster
            direction_x: X direction of the ray caster
            direction_y: Y direction of the ray caster
        """

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

        self.lidar_id = LidarSensor.nb_lidar_sensors
        LidarSensor.nb_lidar_sensors += 1

    @qtSlot()
    def update_hit(self):
        """
        Store the distance of the closest obstacle in the shared memory segment.
        """
        super(LidarSensor, self).update_hit()
        if Sensor.shm_data:
            dist = 65535
            if self.hit:
                dist = self.hit.distance()
                dist += math.dist((0, 0), (self.origin_x, self.origin_y))
            Sensor.shm_data.lidar[self.lidar_id] = int(dist)
        self.update_impact()

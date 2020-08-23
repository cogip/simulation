import math
from pathlib import Path
from typing import Union

from PySide2.QtCore import Slot as qtSlot
from PySide2 import QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DExtras import Qt3DExtras

from cogip.assetentity import AssetEntity
from cogip.models import DynObstacleList
from cogip.sensor import ToFSensor, LidarSensor


class RobotEntity(AssetEntity):
    def __init__(
            self,
            asset_path: Union[Path, str],
            asset_name: str = None,
            enable_tof_sensors: bool = True,
            enable_lidar_sensors: bool = True):
        super(RobotEntity, self).__init__(asset_path, asset_name)
        self.enable_tof_sensors = enable_tof_sensors
        self.enable_lidar_sensors = enable_lidar_sensors
        self.tof_sensors = []
        self.lidar_sensors = []
        self.dyn_obstacles_pool = []

    def post_init(self):
        super(RobotEntity, self).post_init()

        if self.enable_tof_sensors:
            self.add_tof_sensors()

        if self.enable_lidar_sensors:
            self.add_lidar_sensors()

    def add_tof_sensors(self):
        sensors_properties = [
            {
                "name": "Back left sensor",
                "origin_x": 135,
                "origin_y": 135
            },
            {
                "name": "Back sensor",
                "origin_x": 0,
                "origin_y": 177
            },
            {
                "name": "Back right sensor",
                "origin_x": -135,
                "origin_y": 135
            },
            {
                "name": "Front right sensor",
                "origin_x": -135,
                "origin_y": -135
            },
            {
                "name": "Front sensor",
                "origin_x": 0,
                "origin_y": -177
            },
            {
                "name": "Front left sensor",
                "origin_x": 135,
                "origin_y": -135
            },
        ]

        # Add sensors
        for prop in sensors_properties:
            if prop:
                sensor = ToFSensor(asset_entity=self, **prop)
                self.tof_sensors.append(sensor)
            else:
                ToFSensor.nb_tof_sensors += 1
                if ToFSensor.shm_data:
                    ToFSensor.shm_data[ToFSensor.nb_tof_sensors] = 65535

    def add_lidar_sensors(self):
        radius = 65.0/2

        sensors_properties = []

        for angle in range(0, 360, 1):
            origin_x = radius * math.cos(math.radians(angle))
            origin_y = radius * math.sin(math.radians(angle))
            sensors_properties.append(
                {
                    "name": f"Lidar {angle}",
                    "origin_x": origin_x,
                    "origin_y": origin_y,
                    "direction_x": origin_x,
                    "direction_y": origin_y,
                }
            )

        # Add sensors
        for prop in sensors_properties:
            sensor = LidarSensor(asset_entity=self, **prop)
            self.lidar_sensors.append(sensor)

    @qtSlot(DynObstacleList)
    def set_dyn_obstacles(self, dyn_obstacles: DynObstacleList) -> None:
        # Store new and already existing dyn obstacles
        current_dyn_obstacles = []

        for dyn_obstacle in dyn_obstacles.__root__:
            if len(dyn_obstacle.__root__) != 4:
                continue
            p0, p1, p2, p3 = dyn_obstacle.__root__
            # Compute obstacle size
            length = math.dist((p0.x, p0.y), (p1.x, p1.y))
            width = math.dist((p1.x, p1.y), (p2.x, p2.y))
            # Compute the obstacle center position
            pos_x = p0.x + (p2.x - p0.x)/2
            pos_y = p0.y + (p2.y - p0.y)/2
            rotation = 90 + math.degrees(math.acos((p0.x-p1.x)/length))

            if len(self.dyn_obstacles_pool):
                dyn_obstacle = self.dyn_obstacles_pool.pop(0)
                dyn_obstacle.setEnabled(True)
            else:
                dyn_obstacle = DynObstacleEntity()
                dyn_obstacle.setParent(self.parentEntity())

            dyn_obstacle.set_position(x=pos_x, y=pos_y, rotation=rotation)
            dyn_obstacle.set_size(length=length, width=width)

            current_dyn_obstacles.append(dyn_obstacle)

        # Disable remaining dyn obstacles
        while len(self.dyn_obstacles_pool):
            dyn_obstacle = self.dyn_obstacles_pool.pop(0)
            dyn_obstacle.setEnabled(False)
            current_dyn_obstacles.append(dyn_obstacle)

        self.dyn_obstacles_pool = current_dyn_obstacles


class DynObstacleEntity(Qt3DCore.QEntity):

    def __init__(self):

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
        self.transform.setTranslation(QtGui.QVector3D(x, y, self.mesh.zExtent()/2))
        self.transform.setRotationZ(rotation)

    def set_size(self, length: int, width: int) -> None:
        self.mesh.setXExtent(width)
        self.mesh.setYExtent(length)

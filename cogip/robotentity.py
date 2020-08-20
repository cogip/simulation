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
        self.dyn_obstacle_entities = {}

    def post_init(self):
        super(RobotEntity, self).post_init()

        if self.enable_tof_sensors:
            self.add_tof_sensors()

        if self.enable_lidar_sensors:
            self.add_lidar_sensors()

    def add_tof_sensors(self):
        sensors_properties = [
            {
                "name": "Front sensor",
                "origin_x": 177,
                "origin_y": 0
            },
            {
                "name": "Front left sensor",
                "origin_x": 135,
                "origin_y": 135
            },
            {
                "name": "Left sensor",
                "origin_x": 0,
                "origin_y": 177
            },
            {
                "name": "Back Left sensor",
                "origin_x": -135,
                "origin_y": 135
            },
            {
                "name": "Back sensor",
                "origin_x": -177,
                "origin_y": 0
            },
            {
                "name": "Back right sensor",
                "origin_x": -135,
                "origin_y": -135
            },
            {
                "name": "Right sensor",
                "origin_x": 0,
                "origin_y": -177
            },
            {
                "name": "Front right",
                "origin_x": 135,
                "origin_y": -135
            }
        ]

        # Add sensors
        for prop in sensors_properties:
            sensor = ToFSensor(asset_entity=self, **prop)
            self.tof_sensors.append(sensor)

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
        new_dyn_obstacle_entities = {}

        for dyn_obstacle in dyn_obstacles.__root__:
            if dyn_obstacle in self.dyn_obstacle_entities.keys():
                new_dyn_obstacle_entities[dyn_obstacle] = self.dyn_obstacle_entities[dyn_obstacle]
                del(self.dyn_obstacle_entities[dyn_obstacle])
                continue

            if len(dyn_obstacle.__root__) != 4:
                continue
            p0, p1, p2, p3 = dyn_obstacle.__root__
            length = math.dist((p0.x, p0.y), (p1.x, p1.y))
            width = math.dist((p1.x, p1.y), (p2.x, p2.y))
            pos_x = min(p0.x, p1.x) + length/2
            pos_y = min(p0.y, p2.y) + width/2
            rotation = 90 + math.degrees(math.acos((p0.x-p1.x)/length))

            self.dyn_obstacle_entity = DynObstacleEntity(
                x=pos_x,
                y=pos_y,
                rotation=rotation,
                length=length,
                width=width
            )
            self.dyn_obstacle_entity.setParent(self.parentEntity())

            new_dyn_obstacle_entities[dyn_obstacle] = self.dyn_obstacle_entity

        # Delete remaining dyn obstacles
        for dyn_obstacle_entitie in self.dyn_obstacle_entities:
            dyn_obstacle_entitie.setParent(None)
            del(dyn_obstacle_entitie)
        self.dyn_obstacle_entities = new_dyn_obstacle_entities


class DynObstacleEntity(Qt3DCore.QEntity):

    def __init__(
            self,
            x: int,
            y: int,
            rotation: int,
            length: int,
            width: int):

        super(DynObstacleEntity, self).__init__()

        self.mesh = Qt3DExtras.QCuboidMesh()
        self.mesh.setXExtent(width)
        self.mesh.setYExtent(length)
        self.mesh.setZExtent(600)
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QDiffuseSpecularMaterial(self)
        # self.material.setAmbient(QtGui.QColor(QtCore.Qt.green))
        self.material.setDiffuse(QtGui.QColor.fromRgb(0, 255, 0, 50))
        self.material.setDiffuse(QtGui.QColor.fromRgb(0, 255, 0, 50))
        self.material.setSpecular(QtGui.QColor.fromRgb(0, 255, 0, 50))
        self.material.setShininess(1.0)
        self.material.setAlphaBlendingEnabled(True)

        self.addComponent(self.material)

        self.transform = Qt3DCore.QTransform(self)
        self.transform.setTranslation(QtGui.QVector3D(x, y, self.mesh.zExtent()/2))
        self.transform.setRotationZ(rotation)
        self.addComponent(self.transform)

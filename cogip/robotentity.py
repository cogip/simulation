import math
from pathlib import Path
from typing import Union

from cogip.assetentity import AssetEntity
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

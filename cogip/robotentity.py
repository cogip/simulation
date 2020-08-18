from pathlib import Path
from typing import Union

from cogip.assetentity import AssetEntity
from cogip.sensor import Sensor


class RobotEntity(AssetEntity):
    def __init__(
            self,
            asset_path: Union[Path, str],
            asset_name: str = None,
            enable_tof_sensors: bool = True):
        super(RobotEntity, self).__init__(asset_path, asset_name)
        self.enable_tof_sensors = enable_tof_sensors
        self.tof_sensors = []

    def post_init(self):
        super(RobotEntity, self).post_init()

        if self.enable_tof_sensors:
            self.add_tof_sensors()

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
            sensor = Sensor(asset_entity=self, **prop)
            self.tof_sensors.append(sensor)

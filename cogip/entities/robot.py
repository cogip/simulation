from cogip.models.models import DynObstacleRect
import math
from pathlib import Path
from typing import Union

from PySide2.QtCore import Slot as qtSlot
from PySide2 import QtCore, QtGui
from PySide2.Qt3DExtras import Qt3DExtras

from cogip.entities.asset import AssetEntity
from cogip.entities.dynobstacle import DynRectObstacleEntity, DynCircleObstacleEntity
from cogip.entities.sensor import ToFSensor, LidarSensor
from cogip.models import DynObstacleList, RobotState


class RobotEntity(AssetEntity):
    """
    The robot entity displayed on the table.

    Used to display the robot and the position to reach.

    Attributes:
        sensors_update_interval: Interval in seconds between each sensors update
    """

    sensors_update_interval: int = 5

    def __init__(
            self,
            asset_path: Union[Path, str],
            asset_name: str = None,
            enable_tof_sensors: bool = True,
            enable_lidar_sensors: bool = True,
            color: QtGui.QColor = None):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].

        Arguments:
            asset_path: Path of the asset file
            asset_name: Name of the entity to identity the usefull entity
                after load the asset file
            enable_tof_sensors: Enable the ToF sensors
            enable_lidar_sensors: Enable the LIDAR sensors
            color: The color of the robot
        """
        super(RobotEntity, self).__init__(asset_path, asset_name)
        self.enable_tof_sensors = enable_tof_sensors
        self.enable_lidar_sensors = enable_lidar_sensors
        self.color = color
        self.tof_sensors = []
        self.lidar_sensors = []
        self.rect_obstacles_pool = []
        self.round_obstacles_pool = []

        # Use a timer to trigger sensors update
        self.sensor_timer = QtCore.QTimer()
        self.sensor_timer.start(RobotEntity.sensors_update_interval)

    def post_init(self):
        """
        Function called once the asset has been loaded.

        Set the color and enable sensors.
        """
        super(RobotEntity, self).post_init()

        if self.color:
            self.material = Qt3DExtras.QDiffuseSpecularMaterial(self)
            self.material.setDiffuse(self.color)
            self.material.setDiffuse(self.color)
            self.material.setSpecular(self.color)
            self.material.setShininess(1.0)
            self.material.setAlphaBlendingEnabled(True)
            self.asset_entity.addComponent(self.material)

        if self.enable_tof_sensors:
            self.add_tof_sensors()

        if self.enable_lidar_sensors:
            self.add_lidar_sensors()

    def add_tof_sensors(self):
        """
        Add ToF sensors to the robot entity.
        """
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
                self.sensor_timer.timeout.connect(sensor.update_hit)
                self.tof_sensors.append(sensor)
            else:
                ToFSensor.nb_tof_sensors += 1
                if ToFSensor.shm_data:
                    ToFSensor.shm_data[ToFSensor.nb_tof_sensors] = 65535

    def add_lidar_sensors(self):
        """
        Add LIDAR sensors to the robot entity,
        one by degree around the top of the robot.
        """

        radius = 65.0/2

        sensors_properties = []

        for i in range(0, 360):
            angle = (360 - i) % 360
            origin_x = radius * math.sin(math.radians(180 - angle))
            origin_y = radius * math.cos(math.radians(180 - angle))
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
            self.sensor_timer.timeout.connect(sensor.update_hit)
            self.lidar_sensors.append(sensor)

    @qtSlot(DynObstacleList)
    def set_dyn_obstacles(self, dyn_obstacles: DynObstacleList) -> None:
        """
        Qt Slot

        Display the dynamic obstacles detected by the robot.

        Reuse already created dynamic obstacles to optimize performance
        and memory consumption.

        Arguments:
            dyn_obstacles: List of obstacles sent by the firmware throught the serial port
        """
        # Store new and already existing dyn obstacles
        current_rect_obstacles = []
        current_round_obstacles = []

        for dyn_obstacle in dyn_obstacles.__root__:
            if isinstance(dyn_obstacle, DynObstacleRect):
                if len(self.rect_obstacles_pool):
                    obstacle = self.rect_obstacles_pool.pop(0)
                    obstacle.setEnabled(True)
                else:
                    obstacle = DynRectObstacleEntity()
                    obstacle.setParent(self.parentEntity())

                obstacle.set_position(x=dyn_obstacle.x, y=dyn_obstacle.y, rotation=dyn_obstacle.angle)
                obstacle.set_size(length=dyn_obstacle.length_y, width=dyn_obstacle.length_x)

                current_rect_obstacles.append(obstacle)
            else:
                # Round obstacle
                if len(self.round_obstacles_pool):
                    obstacle = self.round_obstacles_pool.pop(0)
                    obstacle.setEnabled(True)
                else:
                    obstacle = DynCircleObstacleEntity()
                    obstacle.setParent(self.parentEntity())

                obstacle.set_position(x=dyn_obstacle.x, y=dyn_obstacle.y, radius=dyn_obstacle.radius)

                current_round_obstacles.append(obstacle)

        # Disable remaining dyn obstacles
        while len(self.rect_obstacles_pool):
            dyn_obstacle = self.rect_obstacles_pool.pop(0)
            dyn_obstacle.setEnabled(False)
            current_rect_obstacles.append(dyn_obstacle)

        while len(self.round_obstacles_pool):
            dyn_obstacle = self.round_obstacles_pool.pop(0)
            dyn_obstacle.setEnabled(False)
            current_round_obstacles.append(dyn_obstacle)

        self.rect_obstacles_pool = current_rect_obstacles
        self.round_obstacles_pool = current_round_obstacles

    @qtSlot(RobotState)
    def new_robot_state(self, new_state: RobotState) -> None:
        """
        Qt slot called to set the robot's new position.

        If sensors are disabled, we consider that this robot represents
        the position to reach.

        Arguments:
            new_state: new robot state
        """
        state = new_state.copy()
        if not self.enable_tof_sensors and not self.enable_lidar_sensors:
            state.pose_current = new_state.pose_order
        super(RobotEntity, self).new_robot_state(state)

        if state.obstacles:
            self.set_dyn_obstacles(state.obstacles)

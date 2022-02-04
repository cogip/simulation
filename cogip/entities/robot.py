from cogip.models.models import DynObstacleRect
import math
from pathlib import Path

from PySide6.QtCore import Slot as qtSlot
from PySide6 import QtCore, QtGui
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras

from cogip import logger
from cogip.entities.asset import AssetEntity
from cogip.entities.dynobstacle import DynRectObstacleEntity, DynCircleObstacleEntity
from cogip.entities.sensor import LidarSensor
from cogip.models import DynObstacleList, RobotState


class RobotEntity(AssetEntity):
    """
    The robot entity displayed on the table.

    Attributes:
        asset_path: Path of the asset file
        asset_name: Interval in seconds between each sensors update
        asset_scale: Scale to apply to the entity after load
        sensors_update_interval: Interval in milliseconds between each sensors update

    """
    asset_path: Path = Path("assets/robot2021.dae")
    asset_name: str = "Scene"
    asset_scale: float = 1000.0
    sensors_update_interval: int = 5

    def __init__(self):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].
        """
        super().__init__(self.asset_path, scale=self.asset_scale)
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
        super().post_init()

        self.asset_entity = self.findChild(Qt3DCore.QEntity, self.asset_name)
        if not self.asset_entity:
            logger.error(f"Entity '{self.asset_name}' not found in {self.asset_path}")
            return

        self.asset_entity.setParent(self)

        if self.scale != 1:
            for comp in self.asset_entity.components():
                if isinstance(comp, Qt3DCore.QTransform):
                    comp.setScale(self.scale)
                    break

        self.add_lidar_sensors()

    def add_lidar_sensors(self):
        """
        Add LIDAR sensors to the robot entity,
        one by degree around the top of the robot.
        """

        radius = 65.0/2

        sensors_properties = []

        for i in range(0, 360):
            angle = (360 - i) % 360
            angle = i
            origin_x = radius * math.sin(math.radians(180 - angle))
            origin_y = radius * math.cos(math.radians(180 - angle))
            origin_x = radius * math.sin(math.radians(angle))
            origin_y = radius * math.cos(math.radians(angle))
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

        Arguments:
            new_state: new robot state
        """
        self.transform_component.setTranslation(
            QtGui.QVector3D(new_state.pose_current.x, new_state.pose_current.y, 0))
        self.transform_component.setRotationZ(new_state.pose_current.O - 90)

        if new_state.obstacles:
            self.set_dyn_obstacles(new_state.obstacles)


class RobotShadowEntity(AssetEntity):
    """
    The robot entity displayed on the table to show the position to reach.

    Attributes:
        asset_path: Path of the asset file
        asset_name: Interval in seconds between each sensors update
        asset_scale: Scale to apply to the entity after load
    """

    asset_path: Path = Path("assets/robot2021.dae")
    asset_name: str = "Scene"
    asset_scale: float = 1000.0

    def __init__(self, color: QtGui.QColor = QtGui.QColor.fromRgb(0, 255, 0, 50)):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].

        Arguments:
            color: The color of the robot
        """
        super().__init__(self.asset_path, scale=self.asset_scale)
        self.color = color

    def post_init(self):
        """
        Function called once the asset has been loaded.

        Set the color and enable sensors.
        """
        super().post_init()

        self.asset_entity = self.findChild(Qt3DCore.QEntity, self.asset_name)
        if not self.asset_entity:
            logger.error(f"Entity '{self.asset_name}' not found in {self.asset_path}")
            return

        self.asset_entity.setParent(self)

        if self.scale != 1:
            for comp in self.asset_entity.components():
                if isinstance(comp, Qt3DCore.QTransform):
                    comp.setScale(self.scale)
                    break

        for material in self.asset_entity.findChildren(Qt3DExtras.QPhongMaterial):
            material.setDiffuse(self.color)
            material.setSpecular(self.color)

    @qtSlot(RobotState)
    def new_robot_state(self, new_state: RobotState) -> None:
        """
        Qt slot called to set the robot's new position to reach.

        Arguments:
            new_state: new robot state
        """
        self.transform_component.setTranslation(
            QtGui.QVector3D(new_state.pose_order.x, new_state.pose_order.y, 0))
        self.transform_component.setRotationZ(new_state.pose_order.O - 90)

from typing import List
import math
from pathlib import Path

from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot
from PySide6 import QtCore, QtGui
from PySide6.Qt3DCore import Qt3DCore

from cogip import logger
from cogip.models import DynObstacleList, DynObstacleRect, Pose, RobotState

from .asset import AssetEntity
from .dynobstacle import DynRectObstacleEntity, DynCircleObstacleEntity
from .robot_order import RobotOrderEntity
from .sensor import LidarSensor


class RobotEntity(AssetEntity):
    """
    The robot entity displayed on the table.

    Attributes:
        asset_path: Path of the asset file
        asset_name: Interval in seconds between each sensors update
        sensors_update_interval: Interval in milliseconds between each sensors update
        lidar_emit_interval: Interval in milliseconds between each Lidar data emission
        lidar_emit_data_signal: Qt Signal emitting Lidar data
        order_robot:: Entity that represents the robot next destination
    """
    asset_path: Path = Path("assets/robot2022.dae")
    asset_name: str = "myscene"
    sensors_update_interval: int = 5
    lidar_emit_interval: int = 20
    lidar_emit_data_signal: qtSignal = qtSignal(list)
    order_robot: "RobotOrderEntity" = None

    def __init__(self):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].
        """
        super().__init__(self.asset_path)
        self.lidar_sensors = []
        self.rect_obstacles_pool = []
        self.round_obstacles_pool = []

        # Use a timer to trigger sensors update
        self.sensors_update_timer = QtCore.QTimer()

        self.lidar_emit_timer = QtCore.QTimer()
        self.lidar_emit_timer.timeout.connect(self.emit_lidar_data)

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

        for comp in self.asset_entity.components():
            if isinstance(comp, Qt3DCore.QTransform):
                comp.setRotationX(0)
                comp.setRotationY(0)
                comp.setRotationZ(0)
                break

        self.add_lidar_sensors()
        self.order_robot = RobotOrderEntity(self.parent())

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
            self.sensors_update_timer.timeout.connect(sensor.update_hit)
            self.lidar_sensors.append(sensor)

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

        for dyn_obstacle in dyn_obstacles:
            if isinstance(dyn_obstacle, DynObstacleRect):
                if len(self.rect_obstacles_pool):
                    obstacle = self.rect_obstacles_pool.pop(0)
                    obstacle.setEnabled(True)
                else:
                    obstacle = DynRectObstacleEntity(self.parentEntity())

                obstacle.set_position(x=dyn_obstacle.x, y=dyn_obstacle.y, rotation=dyn_obstacle.angle)
                obstacle.set_size(length=dyn_obstacle.length_y, width=dyn_obstacle.length_x)
                obstacle.set_bounding_box(dyn_obstacle.bb)

                current_rect_obstacles.append(obstacle)
            else:
                # Round obstacle
                if len(self.round_obstacles_pool):
                    obstacle = self.round_obstacles_pool.pop(0)
                    obstacle.setEnabled(True)
                else:
                    obstacle = DynCircleObstacleEntity(self.parentEntity())

                obstacle.set_position(x=dyn_obstacle.x, y=dyn_obstacle.y, radius=dyn_obstacle.radius)
                obstacle.set_bounding_box(dyn_obstacle.bb)

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

    @qtSlot(Pose)
    def new_robot_pose(self, new_pose: Pose) -> None:
        """
        Qt slot called to set the robot's new pose.

        Arguments:
            new_pose: new robot pose
        """
        self.transform_component.setTranslation(
            QtGui.QVector3D(new_pose.x, new_pose.y, 0))
        self.transform_component.setRotationZ(new_pose.O - 90)

    @qtSlot(RobotState)
    def new_robot_state(self, new_state: RobotState) -> None:
        """
        Qt slot called to set the robot's new position.

        Arguments:
            new_state: new robot state
        """
        if self.order_robot:
            self.order_robot.transform.setTranslation(
                QtGui.QVector3D(new_state.pose_order.x, new_state.pose_order.y, 0))
            self.order_robot.transform.setRotationZ(new_state.pose_order.O - 90)

    def start_lidar_emulation(self) -> None:
        """
        Start timers triggering sensors update and Lidar data emission.
        """
        self.sensors_update_timer.start(RobotEntity.sensors_update_interval)
        self.lidar_emit_timer.start(RobotEntity.lidar_emit_interval)

    def stop_lidar_emulation(self) -> None:
        """
        Stop timers triggering sensors update and Lidar data emission.
        """
        self.sensors_update_timer.stop()
        self.lidar_emit_timer.stop()

    def lidar_data(self) -> List[int]:
        """
        Return a list of distances for each 360 Lidar angles.
        """
        return [sensor.distance for sensor in self.lidar_sensors]

    @qtSlot()
    def emit_lidar_data(self) -> None:
        """
        Qt Slot called to emit Lidar data.
        """
        self.lidar_emit_data_signal.emit(self.lidar_data())

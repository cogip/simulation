from __future__ import annotations
import math
from pathlib import Path

from PySide6 import QtCore, QtGui
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from cogip.models import Pose
from .asset import AssetEntity
from .robot_order import RobotOrderEntity
from .sensor import LidarSensor, Sensor


class RobotEntity(AssetEntity):
    """
    The robot entity displayed on the table.

    Attributes:
        asset_path: Path of the asset file
        sensors_update_interval: Interval in milliseconds between each sensors update
        lidar_emit_interval: Interval in milliseconds between each Lidar data emission
        lidar_emit_data_signal: Qt Signal emitting Lidar data
        order_robot:: Entity that represents the robot next destination
    """
    asset_path: Path = Path("assets/robot2023.dae")
    sensors_update_interval: int = 5
    lidar_emit_interval: int = 20
    lidar_emit_data_signal: qtSignal = qtSignal(int, list)
    order_robot: RobotOrderEntity = None

    def __init__(self, robot_id: int, parent: Qt3DCore.QEntity | None = None):
        """
        Class constructor.

        Inherits [AssetEntity][cogip.entities.asset.AssetEntity].
        """
        super().__init__(self.asset_path, parent=parent)
        self.robot_id = robot_id
        self.lidar_sensors = []
        self.rect_obstacles_pool = []
        self.round_obstacles_pool = []

        self.beacon_entity = Qt3DCore.QEntity(self)
        self.beacon_mesh = Qt3DExtras.QCylinderMesh(self.beacon_entity)
        self.beacon_mesh.setLength(80)
        self.beacon_mesh.setRadius(40)
        self.beacon_entity.addComponent(self.beacon_mesh)

        self.beacon_transform = Qt3DCore.QTransform(self.beacon_entity)
        self.beacon_transform.setTranslation(QtGui.QVector3D(0, 0, 350 + self.beacon_mesh.length() / 2))
        self.beacon_transform.setRotationX(90)
        self.beacon_entity.addComponent(self.beacon_transform)

        # Create a layer used by sensors to activate detection on the beacon
        self.beacon_entity.layer = Qt3DRender.QLayer(self.beacon_entity)
        self.beacon_entity.layer.setRecursive(True)
        self.beacon_entity.layer.setEnabled(True)
        self.beacon_entity.addComponent(self.beacon_entity.layer)

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

        self.add_lidar_sensors()
        self.order_robot = RobotOrderEntity(self.parent())

        Sensor.add_obstacle(self.beacon_entity)

    def add_lidar_sensors(self):
        """
        Add LIDAR sensors to the robot entity,
        one by degree around the top of the robot.
        """

        radius = 65.0 / 2

        sensors_properties = []

        for i in range(0, 360):
            angle = (360 - i) % 360
            origin_x = radius * math.sin(math.radians(90 - angle))
            origin_y = radius * math.cos(math.radians(90 - angle))
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

    @qtSlot(Pose)
    def new_robot_pose_current(self, new_pose: Pose) -> None:
        """
        Qt slot called to set the robot's new pose current.

        Arguments:
            new_pose: new robot pose
        """
        self.transform_component.setTranslation(
            QtGui.QVector3D(new_pose.x, new_pose.y, 0)
        )
        self.transform_component.setRotationZ(new_pose.O)

    @qtSlot(Pose)
    def new_robot_pose_order(self, new_pose: Pose) -> None:
        """
        Qt slot called to set the robot's new pose order.

        Arguments:
            new_pose: new robot pose
        """
        if self.order_robot:
            self.order_robot.transform.setTranslation(
                QtGui.QVector3D(new_pose.x, new_pose.y, 0)
            )
            self.order_robot.transform.setRotationZ(new_pose.O)

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

    def lidar_data(self) -> list[int]:
        """
        Return a list of distances for each 360 Lidar angles.
        """
        return [sensor.distance for sensor in self.lidar_sensors]

    @qtSlot()
    def emit_lidar_data(self) -> None:
        """
        Qt Slot called to emit Lidar data.
        """
        self.lidar_emit_data_signal.emit(self.robot_id, self.lidar_data())

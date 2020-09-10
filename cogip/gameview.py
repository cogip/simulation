from pathlib import Path

from pydantic import ValidationError

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot

from cogip.assetentity import AssetEntity
from cogip.obstacleentity import ObstacleEntity
from cogip import models


def create_ligth_entity(x: float, y: float, z: float) -> Qt3DCore.QEntity:
    light_entity = Qt3DCore.QEntity()

    light = Qt3DRender.QPointLight(light_entity)

    light.setColor(QtGui.QColor(QtCore.Qt.white))

    light.setIntensity(1)
    light_entity.addComponent(light)

    light_transform = Qt3DCore.QTransform(light_entity)
    light_transform.setTranslation(QtGui.QVector3D(x, y, z))
    light_entity.addComponent(light_transform)

    return light_entity


class GameView(QtWidgets.QWidget):

    ready = qtSignal()
    new_move_delta = qtSignal(QtGui.QVector3D)

    def __init__(self):
        super(GameView, self).__init__()

        self.obstacle_entities = []

        # Create the view and set it as the widget layout
        self.view = Qt3DExtras.Qt3DWindow()
        screen_size = self.view.screen().size()
        self.container = self.createWindowContainer(self.view)
        self.container.setMinimumSize(QtCore.QSize(800, 600))
        self.container.setMaximumSize(screen_size)
        self.container.setFocusPolicy(QtCore.Qt.NoFocus)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.container)
        self.setLayout(layout)

        picking_settings = self.view.renderSettings().pickingSettings()
        # picking_settings.setPickMethod(Qt3DRender.QPickingSettings.PrimitivePicking)
        picking_settings.setPickMethod(Qt3DRender.QPickingSettings.TrianglePicking)
        picking_settings.setPickResultMode(Qt3DRender.QPickingSettings.NearestPick)
        picking_settings.setPickResultMode(Qt3DRender.QPickingSettings.AllPicks)

        # Create root entity
        self.root_entity = Qt3DCore.QEntity()
        self.view.setRootEntity(self.root_entity)

        # Init Camera
        self.camera_entity = self.view.camera()  # type: Qt3DRender.QCamera
        # QCameraLens::setPerspectiveProjection(float fieldOfView, float aspectRatio, float nearPlane, float farPlane)
        self.camera_entity.lens().setPerspectiveProjection(45.0, 16.0 / 9.0, 0.1, 20000.0)
        self.camera_entity.setUpVector(QtGui.QVector3D(0, 0, 1))
        self.camera_entity.setPosition(QtGui.QVector3D(3000, 3000, 3000))
        self.camera_entity.setViewCenter(QtGui.QVector3D(0, 1000, 0))

        # Create camera controller entity
        self.camera_controller = Qt3DExtras.QOrbitCameraController(self.root_entity)
        # self.camera_controller = Qt3DExtras.QFirstPersonCameraController(self.root_entity)
        self.camera_controller.setCamera(self.camera_entity)
        self.camera_controller.setLinearSpeed(10000)  # default = 10
        # self.camera_controller.setLookSpeed(1000)  # default = 180

        # Create light
        self.light_entity = create_ligth_entity(20000, 20000, 20000)
        self.light_entity.setParent(self.root_entity)
        self.light_entity2 = create_ligth_entity(20000, -20000, 20000)
        self.light_entity2.setParent(self.root_entity)

        # Add a plane mesh with object picker to help moving obstacles
        # with mouse drag and drop
        self.plane_entity = Qt3DCore.QEntity()
        self.plane_entity.setParent(self.root_entity)

        self.plane_mesh = Qt3DExtras.QPlaneMesh()
        self.plane_mesh.setHeight(8000)
        self.plane_mesh.setWidth(10000)
        self.plane_entity.addComponent(self.plane_mesh)

        self.plane_material = Qt3DExtras.QDiffuseSpecularMaterial()
        self.plane_material.setDiffuse(QtGui.QColor.fromRgb(255, 0, 0, 0))
        self.plane_material.setDiffuse(QtGui.QColor.fromRgb(255, 0, 0, 0))
        self.plane_material.setSpecular(QtGui.QColor.fromRgb(255, 0, 0, 0))
        self.plane_material.setShininess(1.0)
        self.plane_material.setAlphaBlendingEnabled(True)
        self.plane_entity.addComponent(self.plane_material)

        self.plane_transform = Qt3DCore.QTransform()
        self.plane_transform.setTranslation(QtGui.QVector3D(0, 1000, 0))
        self.plane_transform.setRotationX(90)
        self.plane_entity.addComponent(self.plane_transform)

        self.plane_picker = Qt3DRender.QObjectPicker()
        self.plane_picker.setDragEnabled(True)
        self.plane_picker.pressed.connect(self.plane_pressed)
        self.plane_picker.released.connect(self.plane_released)
        self.plane_picker.moved.connect(self.plane_moved)
        self.plane_entity.addComponent(self.plane_picker)
        self.plane_intersection = None

    def add_asset(self, asset: AssetEntity) -> None:
        asset.setParent(self.root_entity)
        asset.ready.connect(self.asset_ready)

    @qtSlot()
    def add_obstacle(
            self,
            x: int = 0,
            y: int = 1000,
            rotation: int = 0,
            **kwargs) -> ObstacleEntity:
        obstacle_entity = ObstacleEntity(self.container, x, y, rotation, **kwargs)
        obstacle_entity.setParent(self.root_entity)
        self.obstacle_entities.append(obstacle_entity)
        obstacle_entity.enable_controller.connect(self.camera_controller.setEnabled)
        self.new_move_delta.connect(obstacle_entity.new_move_delta)
        return obstacle_entity

    @qtSlot(Path)
    def load_obstacles(self, filename: Path):
        try:
            obstacle_models = models.ObstacleList.parse_file(filename)
            for obstacle_model in obstacle_models:
                self.add_obstacle(**obstacle_model.dict())
        except ValidationError:
            pass

    @qtSlot(Path)
    def save_obstacles(self, filename: Path):
        obstacle_models = models.ObstacleList.parse_obj([])
        for obstacle_entity in self.obstacle_entities:
            obstacle_models.append(obstacle_entity.get_model())
        with filename.open('w') as fd:
            fd.write(obstacle_models.json(indent=2))

    def game_ready(self) -> bool:
        child_assets_not_ready = [
            child for child in self.root_entity.findChildren(AssetEntity) if not child.asset_ready]
        return len(child_assets_not_ready) == 0

    @qtSlot()
    def asset_ready(self):
        if self.game_ready():
            self.ready.emit()

    @qtSlot(Qt3DRender.QPickEvent)
    def plane_pressed(self, pick: Qt3DRender.QPickEvent):
        self.plane_intersection = pick.worldIntersection()

    @qtSlot(Qt3DRender.QPickEvent)
    def plane_moved(self, pick: Qt3DRender.QPickEvent):
        new_intersection = pick.worldIntersection()
        delta = new_intersection - self.plane_intersection
        delta.setZ(0)
        self.new_move_delta.emit(delta)
        self.plane_intersection = new_intersection

    @qtSlot(Qt3DRender.QPickEvent)
    def plane_released(self, pick: Qt3DRender.QPickEvent):
        self.plane_intersection = None
        self.new_move_delta.emit(None)

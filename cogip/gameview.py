from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot

from cogip.assetentity import AssetEntity
from cogip.obstacleentity import ObstacleEntity


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

    def __init__(self):
        super(GameView, self).__init__()

        # Create the view and set it as the widget layout
        self.view = Qt3DExtras.Qt3DWindow()
        screen_size = self.view.screen().size()
        self.container = self.createWindowContainer(self.view)
        self.container.setMinimumSize(QtCore.QSize(1280, 960))
        self.container.setMaximumSize(screen_size)
        self.container.setFocusPolicy(QtCore.Qt.NoFocus)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.container)
        self.setLayout(layout)

        picking_settings = self.view.renderSettings().pickingSettings()
        # picking_settings.setPickMethod(Qt3DRender.QPickingSettings.PrimitivePicking)
        picking_settings.setPickMethod(Qt3DRender.QPickingSettings.TrianglePicking)
        picking_settings.setPickResultMode(Qt3DRender.QPickingSettings.NearestPick)

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
        obstacle = ObstacleEntity(self.container, x, y, rotation, **kwargs)
        obstacle.setParent(self.root_entity)
        return obstacle

    def game_ready(self) -> bool:
        child_assets_not_ready = [
            child for child in self.root_entity.findChildren(AssetEntity) if not child.asset_ready]
        return len(child_assets_not_ready) == 0

    @qtSlot()
    def asset_ready(self):
        if self.game_ready():
            self.ready.emit()

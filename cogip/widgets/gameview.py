import json
import math
from pathlib import Path
import timeit
from typing import Any, Dict, List

from pydantic import ValidationError
from pydantic.json import pydantic_encoder
from pydantic.tools import parse_file_as

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DRender import Qt3DRender
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.QtCore import Signal as qtSignal

from cogip.entities.asset import AssetEntity
from cogip.entities.obstacle import ObstacleEntity
from cogip.entities.path import PathEntity
from cogip.entities.robot_manual import RobotManualEntity
from cogip.entities.sample import create_samples
from cogip.models import models


class EventFilter(QtCore.QObject):
    """
    Event filter registered on the 3D Window.

    Filter all mouse and keyboard events related to moving the scene
    in front of the camera.
    """
    def __init__(self, parent: "GameView"):
        """
        Class constructor
        """
        super().__init__(parent)
        self.game_view = parent
        self._last_mouse_pos = None

    def eventFilter(self, source, event) -> bool:
        """
        Required event filter function.
        """
        if isinstance(event, QtGui.QKeyEvent):
            key: QtCore.Qt.Key = event.key()
            modifiers: QtCore.Qt.KeyboardModifiers = event.modifiers()

            if modifiers == QtCore.Qt.NoModifier:
                if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Q]:
                    self.game_view.translate(-10, 0, 0)
                elif key in [QtCore.Qt.Key_Right, QtCore.Qt.Key_D]:
                    self.game_view.translate(10, 0, 0)
                elif key in [QtCore.Qt.Key_Down, QtCore.Qt.Key_S]:
                    self.game_view.translate(0, -10, 0)
                elif key in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Z]:
                    self.game_view.translate(0, 10, 0)
                elif key == QtCore.Qt.Key_Space:
                    self.game_view.top_view()
                elif key == QtCore.Qt.Key_Return:
                    self.game_view.default_view()
                else:
                    return False
                return True

            elif modifiers == QtCore.Qt.ShiftModifier:
                if key in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Z]:
                    self.game_view.rotate(-1, 0, 0)
                elif key in [QtCore.Qt.Key_Down, QtCore.Qt.Key_S]:
                    self.game_view.rotate(1, 0, 0)
                elif key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Q]:
                    self.game_view.rotate(0, -1, 0)
                elif key in [QtCore.Qt.Key_Right, QtCore.Qt.Key_D]:
                    self.game_view.rotate(0, 1, 0)
                else:
                    return False
                return True

            elif modifiers == QtCore.Qt.ControlModifier:
                if key in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Q]:
                    self.game_view.rotate(0, 0, -1)
                elif key in [QtCore.Qt.Key_Right, QtCore.Qt.Key_D]:
                    self.game_view.rotate(0, 0, 1)
                elif key in [QtCore.Qt.Key_Down, QtCore.Qt.Key_S]:
                    self.game_view.translate(0, 0, -20)
                elif key in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Z]:
                    self.game_view.translate(0, 0, 20)
                else:
                    return False

            else:
                return False

        elif isinstance(event, QtGui.QWheelEvent):
            self.game_view.translate(0, 0, event.angleDelta().y() / 5)

        elif isinstance(event, QtGui.QMouseEvent):
            new_pos = event.globalPos()
            if not self._last_mouse_pos:
                self._last_mouse_pos = new_pos
            new_pos = event.globalPos()
            delta = new_pos - self._last_mouse_pos
            self._last_mouse_pos = new_pos

            if event.type() == QtCore.QEvent.MouseMove:
                if event.buttons() == Qt3DRender.QPickEvent.MiddleButton:
                    self.game_view.rotate(0, 0, (delta.x() + delta.y())/2)
                elif event.buttons() == Qt3DRender.QPickEvent.RightButton:
                    self.game_view.rotate(delta.y(), delta.x(), 0)
                else:
                    return False
            else:
                return False
        else:
            return False

        return True


class GameView(QtWidgets.QWidget):
    """
    The `GameView` class is a [`QWidget`](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html)
    containing a [`Qt3DWindow`](https://doc.qt.io/qtforpython-6/PySide6/Qt3DExtras/Qt3DWindow.html)
    used to display all the game element, like table, robot and obstacles.

    It also contains an horizontal plane entity with a invisible
    [`QPlaneMesh`](https://doc.qt.io/qtforpython-6/PySide6/Qt3DExtras/QPlaneMesh.html).
    This plane is has a [`QObjectPicker`](https://doc.qt.io/qtforpython-6/PySide6/Qt3DRender/QObjectPicker.html)
    to detect mouse clicks, to help grabbing and moving entities on the horizontal plane.

    Attributes:
        ground_image: image to display on the table floor
        obstacle_entities: List of obstacles
        sample_entities: List of samples
        plane_intersection: last active intersection of plane picker in world coordinates
        mouse_enabled: True to authorize translation and rotation of the scene using the mouse,
            False when an other object (obstacle, manual robot, ...) is picked.
        new_move_delta: signal emitted to movable entities when a mouse drag is detected
    """
    ground_image: Path = Path("assets/ground2022.png")
    obstacle_entities: List[ObstacleEntity] = []
    sample_entities: List[models.Sample] = []
    plane_intersection: QtGui.QVector3D = None
    mouse_enabled: bool = True
    new_move_delta: qtSignal = qtSignal(QtGui.QVector3D)

    def __init__(self):
        """
        Create all entities required in the view:

          - the `Qt3DWindow` to display the scene
          - the camera and all controls to move the scene in front of the camera
          - the lights to have a good lightning of the scene
          - the plane entity to help moving obstacles
        """
        super().__init__()

        # Create the 3D window and set it as the widget layout
        self.view = Qt3DExtras.Qt3DWindow()
        self.view.installEventFilter(EventFilter(self))
        self.container = self.createWindowContainer(self.view)
        self.container.setMinimumSize(QtCore.QSize(400, 400))
        self.container.setFocusPolicy(QtCore.Qt.NoFocus)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.container)
        self.setLayout(layout)

        picking_settings = self.view.renderSettings().pickingSettings()
        picking_settings.setPickMethod(Qt3DRender.QPickingSettings.TrianglePicking)
        picking_settings.setPickResultMode(Qt3DRender.QPickingSettings.AllPicks)

        # Create root entity
        self.root_entity = Qt3DCore.QEntity()
        self.view.setRootEntity(self.root_entity)

        self.root_transform = Qt3DCore.QTransform()
        self.root_entity.addComponent(self.root_transform)
        self.default_view()

        # Create an object picker to catch mouse clicks on root entity
        self.root_picker = Qt3DRender.QObjectPicker()
        self.root_picker.setDragEnabled(True)
        self.root_picker.pressed.connect(self.pressed)
        self.root_picker.moved.connect(self.moved)
        self.root_entity.addComponent(self.root_picker)

        # Create scene entity
        self.scene_entity = Qt3DCore.QEntity(self.root_entity)

        self.scene_transform = Qt3DCore.QTransform()
        self.scene_entity.addComponent(self.scene_transform)
        self.scene_transform.setTranslation(QtGui.QVector3D(0, -1000, 0))

        self.path: PathEntity = PathEntity(parent=self.scene_entity)

        # Init Camera
        self.camera_entity: Qt3DRender.QCamera = self.view.camera()
        self.camera_entity.lens().setPerspectiveProjection(45.0, 16.0 / 9.0, 0.1, 10000.0)
        self.camera_entity.setUpVector(QtGui.QVector3D(0, 0, 1))
        self.camera_entity.setPosition(QtGui.QVector3D(0, 0, 10))
        self.camera_entity.setViewCenter(QtGui.QVector3D(0, 0, 0))

        # Create lights
        self.light_entity = create_ligth_entity(self.root_entity, 5000, 5000, 5000)
        self.light_entity2 = create_ligth_entity(self.root_entity, -5000, 5000, 5000)

        # Create object picker
        self.create_object_picker()

        # Add image on table floor
        self.add_ground_image()

        self.start_time = timeit.default_timer()

    def enable_mouse(self, enable: bool) -> None:
        self.mouse_enabled = enable

    def translate(self, x: int, y: int, z: int) -> None:
        self.root_transform.setTranslation(
            QtGui.QVector3D(
                max(-1500, min(1500, self.root_transform.translation().x() + x)),
                max(-1000, min(1000, self.root_transform.translation().y() + y)),
                max(-5000, min(-10, self.root_transform.translation().z() + z))
            )
        )

    def rotate(self, x: int, y: int, z: int) -> None:
        self.root_transform.setRotationX((self.root_transform.rotationX() + x) % 360),
        self.root_transform.setRotationY((self.root_transform.rotationY() + y) % 360),
        self.root_transform.setRotationZ((self.root_transform.rotationZ() - z) % 360)

    def top_view(self) -> None:
        self.root_transform.setRotationX(0),
        self.root_transform.setRotationY(0),
        self.root_transform.setRotationZ(180)
        self.root_transform.setTranslation(QtGui.QVector3D(0, 0, -4000))

    def default_view(self) -> None:
        self.root_transform.setRotationX(-50)
        self.root_transform.setRotationY(0)
        self.root_transform.setRotationZ(210)
        self.root_transform.setTranslation(QtGui.QVector3D(0, 0, -5000))

    def add_asset(self, asset: AssetEntity) -> None:
        """
        Add an asset (like [TableEntity][cogip.entities.asset.AssetEntity]
        or [RobotEntity][cogip.entities.robot.RobotEntity]) in the 3D view.

        Argument:
            asset: The asset entity to add to the vew
        """
        asset.setParent(self.scene_entity)
        asset.ready.connect(self.asset_ready)

    def add_obstacle(
            self,
            x: int = 0,
            y: int = 1000,
            rotation: int = 0,
            **kwargs) -> ObstacleEntity:
        """
        Create a new obstacle in the 3D view.

        Arguments:
            x: X position
            y: Y position
            rotation: Rotation

        Return:
            The obstacle entity
        """
        obstacle_entity = ObstacleEntity(self.container, x, y, rotation, **kwargs)
        obstacle_entity.setParent(self.scene_entity)
        self.obstacle_entities.append(obstacle_entity)
        obstacle_entity.enable_controller.connect(self.enable_mouse)
        self.new_move_delta.connect(obstacle_entity.new_move_delta)
        return obstacle_entity

    def load_obstacles(self, filename: Path):
        """
        Load obstables from a JSON file.

        Arguments:
            filename: path of the JSON file
        """
        try:
            obstacle_models = models.ObstacleList.parse_file(filename)
            for obstacle_model in obstacle_models:
                self.add_obstacle(**obstacle_model.dict())
        except ValidationError:
            pass

    def save_obstacles(self, filename: Path):
        """
        Save obstables to a JSON file.

        Arguments:
            filename: path of the JSON file
        """
        obstacle_models = models.ObstacleList.parse_obj([])
        for obstacle_entity in self.obstacle_entities:
            obstacle_models.append(obstacle_entity.get_model())
        with filename.open('w') as fd:
            fd.write(obstacle_models.json(indent=2))

    def load_samples(self, filename: Path):
        """
        Load samples from a JSON file.

        Arguments:
            filename: path of the JSON file
        """
        try:
            sample_models = parse_file_as(List[models.Sample], filename)
            for sample_model in sample_models:
                self.sample_entities[sample_model.id].update_from_model(sample_model)
        except ValidationError:
            pass

    def save_samples(self, filename: Path):
        """
        Save samples to a JSON file.

        Arguments:
            filename: path of the JSON file
        """
        sample_models = []
        for sample_entity in self.sample_entities.values():
            sample_models.append(sample_entity.get_model())
        with filename.open('w') as fd:
            fd.write(json.dumps(sample_models, default=pydantic_encoder, indent=2))

    def asset_ready(self):
        """
        Create samples when all assets are ready (loading assets is done in background).
        """
        child_assets_not_ready = [
            child
            for child in self.scene_entity.findChildren(AssetEntity)
            if not child.asset_ready
        ]
        if len(child_assets_not_ready) == 0:
            self.sample_entities = create_samples(self.scene_entity, self.container)
            for sample in self.sample_entities.values():
                sample.enable_controller.connect(self.enable_mouse)
                self.new_move_delta.connect(sample.new_move_delta)

            self.robot_manual = RobotManualEntity(self.scene_entity, self.container)
            self.robot_manual.enable_controller.connect(self.enable_mouse)
            self.new_move_delta.connect(self.robot_manual.new_move_delta)

            print(f"Load time of assets: {timeit.default_timer() - self.start_time:0.3f}s")

    def plane_pressed(self, pick: Qt3DRender.QPickEvent):
        """
        Record the intersection between the mouse pointer and the plane entity,
        on the `pressed` mouse event, in world coordinate.
        """
        if pick.buttons() != Qt3DRender.QPickEvent.LeftButton:
            return

        self.plane_intersection = pick.worldIntersection()

    def plane_moved(self, pick: Qt3DRender.QPickEvent):
        """
        Compute the translation on the plane entity between the
        current `moved` mouse event and the previous one.

        Emit the `new_move_delta` signal to update the corresponding asset's position.
        """
        if pick.buttons() != Qt3DRender.QPickEvent.LeftButton:
            return

        new_intersection = pick.worldIntersection()
        delta: QtGui.QVector3D = new_intersection - self.plane_intersection
        delta.setZ(0)
        rot_z = self.root_transform.rotationZ()
        delta = QtGui.QVector3D(
            delta.x()*math.cos(math.radians(rot_z)) + delta.y()*math.sin(math.radians(rot_z)),
            delta.y()*math.cos(math.radians(rot_z)) - delta.x()*math.sin(math.radians(rot_z)),
            0
        )
        self.new_move_delta.emit(delta)
        self.plane_intersection = new_intersection

    def plane_released(self, pick: Qt3DRender.QPickEvent):
        """
        Emit the `new_move_delta` signal with `None` argument,
        on `released` mouse event, to notify that mouse button was released
        and no further moves will happen until next `pressed` mouse event.
        """
        self.plane_intersection = None
        self.new_move_delta.emit(None)

    def new_robot_state(self, new_state: models.RobotState) -> None:
        """
        Function called when robot state is updated.
        Update computed path.

        Arguments:
            new_state: new robot state
        """
        for vertex in new_state.path:
            vertex.z = 20
        self.path.set_points(new_state.path)

    def pressed(self, pick: Qt3DRender.QPickEvent):
        """
        Function called on a ```pressed``` mouse event on the sample.

        Emit a signal to disable the camera controller before moving the sample.
        """
        self.last_mouse_pos = pick.worldIntersection()

    def moved(self, pick: Qt3DRender.QPickEvent):
        """
        Function called on a ```moved``` mouse event on the sample.

        Just record that the sample is moving, the translation is computed
        in the [GameView][cogip.widgets.gameview.GameView] object.
        """

        if not self.mouse_enabled:
            return

        new_pos = pick.worldIntersection()
        delta = new_pos - self.last_mouse_pos
        self.last_mouse_pos = new_pos

        if pick.buttons() == Qt3DRender.QPickEvent.LeftButton:
            self.translate(delta.x(), delta.y(), 0)

    def create_object_picker(self):
        """
        Add a plane mesh with object picker to help moving objets with mouse drag and drop.
        """
        self.plane_entity = Qt3DCore.QEntity(self.scene_entity)

        plane_mesh = Qt3DExtras.QPlaneMesh(self.plane_entity)
        plane_mesh.setHeight(8000)
        plane_mesh.setWidth(10000)
        self.plane_entity.addComponent(plane_mesh)

        plane_transform = Qt3DCore.QTransform(self.plane_entity)
        plane_transform.setTranslation(QtGui.QVector3D(0, 1000, 0))
        plane_transform.setRotationX(90)
        self.plane_entity.addComponent(plane_transform)

        plane_picker = Qt3DRender.QObjectPicker(self.plane_entity)
        plane_picker.setDragEnabled(True)
        plane_picker.pressed.connect(self.plane_pressed)
        plane_picker.released.connect(self.plane_released)
        plane_picker.moved.connect(self.plane_moved)
        self.plane_entity.addComponent(plane_picker)

    def add_ground_image(self) -> None:
        """
        Add a plane to display the ground image
        """
        self.ground_entity = Qt3DCore.QEntity(self.scene_entity)

        ground_mesh = Qt3DExtras.QPlaneMesh(self.ground_entity)
        ground_mesh.setHeight(2000)
        ground_mesh.setWidth(3000)
        self.ground_entity.addComponent(ground_mesh)

        ground_material = Qt3DExtras.QTextureMaterial(self.ground_entity)

        ground_texture = Qt3DRender.QTexture2D(ground_material)
        ground_texture_image = Qt3DRender.QTextureImage(ground_texture)
        ground_texture_image.setSource(QtCore.QUrl(f"file:{self.ground_image}"))
        ground_texture_image.setMirrored(False)
        ground_texture.addTextureImage(ground_texture_image)
        ground_material.setTexture(ground_texture)
        self.ground_entity.addComponent(ground_material)

        ground_transform = Qt3DCore.QTransform(self.ground_entity)
        ground_transform.setRotationX(-90)
        ground_transform.setRotationY(180)
        ground_transform.setTranslation(QtGui.QVector3D(0, 1000, 0))
        self.ground_entity.addComponent(ground_transform)


def create_ligth_entity(parent: Qt3DCore.QEntity, x: float, y: float, z: float) -> Qt3DCore.QEntity:
    """
    Create a ligth entity at the position specified in arguments.

    Arguments:
        parent: parent entity
        x: X position
        y: Y position
        z: Z position

    Return:
        The light entity
    """
    light_entity = Qt3DCore.QEntity(parent)

    light = Qt3DRender.QPointLight(light_entity)
    light.setColor(QtGui.QColor(QtCore.Qt.white))
    light.setIntensity(1)
    light_entity.addComponent(light)

    light_transform = Qt3DCore.QTransform(light_entity)
    light_transform.setTranslation(QtGui.QVector3D(x, y, z))
    light_entity.addComponent(light_transform)

    return light_entity

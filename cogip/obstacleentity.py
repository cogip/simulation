from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot

from cogip.sensor import Sensor
from cogip import models


class ObstacleEntity(Qt3DCore.QEntity):
    """
    An obstacle on the table.

    It is represented as a cube ([QCuboidMesh](https://doc.qt.io/qtforpython/PySide2/Qt3DExtras/QCuboidMesh.html)).

    When selected with a mouse click, a property window is displayed
    to modify the obstacle properties.

    The obstacle can also be moved using the mouse.

    Attributes:
        enable_controller: Qt signal used to disable the camera controller
            when moving the obstacle using the mouse
    """

    enable_controller = qtSignal(bool)

    def __init__(
            self,
            parent_widget: QtWidgets.QWidget,
            x: int = 0,
            y: int = 1000,
            rotation: int = 0,
            length: int = 200,
            width: int = 200,
            height: int = 600):
        """
        Class constructor.

        Arguments:
            parent_widget: Parent widget
            x: X position
            y: Y position
            rotation: Rotation
            length: Length
            width: Width
            height: Height
        """
        super(ObstacleEntity, self).__init__()

        self.parent_widget = parent_widget

        self.mesh = Qt3DExtras.QCuboidMesh()
        self.mesh.setXExtent(width)
        self.mesh.setYExtent(length)
        self.mesh.setZExtent(height)
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QPhongMaterial(self)
        self.addComponent(self.material)

        self.transform = Qt3DCore.QTransform(self)
        self.transform.setTranslation(QtGui.QVector3D(x, y, self.mesh.zExtent()/2))
        self.transform.setRotationZ(rotation)
        self.addComponent(self.transform)

        self.picker = Qt3DRender.QObjectPicker()
        self.picker.setDragEnabled(True)
        self.picker.pressed.connect(self.pressed_obstacle)
        self.picker.released.connect(self.released_obstacle)
        self.picker.moved.connect(self.moved_obstacle)
        self.addComponent(self.picker)

        self.moving = False

        self.mesh.zExtentChanged.connect(self.updateZTranslation)

        # Create a layer used by sensors to activate detection on the obstacles
        self.layer = Qt3DRender.QLayer(self)
        self.layer.setRecursive(True)
        self.layer.setEnabled(True)
        self.addComponent(self.layer)

        # Create properties dialog
        self.properties = ObstacleProperties(self.parent_widget, self)

        Sensor.add_obstacle(self)

    @qtSlot(float)
    def updateZTranslation(self, zExtent: float):
        """
        Qt Slot

        Update the Z position based on the obstacle heigth.
        This function is called each time the height is modified
        to set the bottom on Z=0.
        """
        translation = self.transform.translation()
        translation.setZ(zExtent/2)
        self.transform.setTranslation(translation)

    @qtSlot(int)
    def setXTranslation(self, x: int):
        """
        Qt Slot

        Set the X position.
        """
        translation = self.transform.translation()
        translation.setX(float(x))
        self.transform.setTranslation(translation)

    @qtSlot(int)
    def setYTranslation(self, y: int):
        """
        Qt Slot

        Set the Y position.
        """
        translation = self.transform.translation()
        translation.setY(float(y))
        self.transform.setTranslation(translation)

    @qtSlot(Qt3DRender.QPickEvent)
    def pressed_obstacle(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```pressed``` mouse event on the obstacle.

        Emit a signal to disable the camera controller before moving the obstacle.
        """
        self.enable_controller.emit(False)

    @qtSlot(Qt3DRender.QPickEvent)
    def released_obstacle(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```released``` mouse event on the obstacle.

        If this event occurs juste after a ```pressed``` event, it is only a mouse click,
        so display the property window.

        Emit a signal to re-enable the camera controller after moving the obstacle.
        """
        if not self.moving:
            if ObstacleProperties.active_properties:
                ObstacleProperties.active_properties.close()
            self.properties.restore_saved_geometry()
            self.properties.show()
            self.properties.raise_()
            self.properties.activateWindow()
            ObstacleProperties.set_active_properties(self.properties)
        self.moving = False
        self.enable_controller.emit(True)

    @qtSlot(Qt3DRender.QPickEvent)
    def moved_obstacle(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```moved``` mouse event on the obstacle.

        Just record that the obstacle is moving, the translation is computed
        in the [GameView][cogip.gameview.GameView] object.
        """
        self.moving = True

    def get_model(self) -> models.Obstacle:
        """
        Returns the [Obstacle][cogip.models.Obstacle] model.
        Used to save the obstacles list.

        Returns:
            The obstacle model
        """
        return models.Obstacle(
            x=self.transform.translation().x(),
            y=self.transform.translation().y(),
            rotation=self.transform.rotationZ(),
            length=self.mesh.yExtent(),
            width=self.mesh.xExtent(),
            height=self.mesh.zExtent()
        )

    @qtSlot(QtGui.QVector3D)
    def new_move_delta(self, delta: QtGui.QVector3D):
        """
        Qt Slot

        Update the obstacle position.

        Arguments:
            delta: The difference between current and new position
        """
        self.move_delta = delta
        if self.moving and delta:
            new_translation = self.transform.translation() + delta
            self.transform.setTranslation(new_translation)
            self.properties.spin_x.setValue(new_translation.x())
            self.properties.spin_y.setValue(new_translation.y())


class ObstacleProperties(QtWidgets.QDialog):
    """
    The property window.

    Each obstacle has its own property window.

    Attributes:
        saved_geometry: The position of the last displayed property window
        active_geometry: The current property window displayed.
    """
    saved_geometry: QtCore.QRect = None
    active_properties: "ObstacleProperties" = None

    def __init__(self, parent: QtWidgets.QWidget, obstacle_entity: ObstacleEntity):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
            obstacle_entity: The related obstacle entity
        """
        super(ObstacleProperties, self).__init__(parent)

        self.obstacle_entity = obstacle_entity
        self.setWindowTitle("Obstacle Properties")
        self.setModal(False)
        self.setMinimumWidth(self.fontMetrics().horizontalAdvance(self.windowTitle()))

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        row = 0

        label_x = QtWidgets.QLabel("X")
        self.spin_x = QtWidgets.QSpinBox()
        self.spin_x.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_x.setMinimum(-1500)
        self.spin_x.setMaximum(1500)
        self.spin_x.setValue(int(self.obstacle_entity.transform.translation().x()))
        self.spin_x.valueChanged.connect(self.obstacle_entity.setXTranslation)
        layout.addWidget(label_x, row, 0)
        layout.addWidget(self.spin_x, row, 1)
        row += 1

        label_y = QtWidgets.QLabel("Y")
        self.spin_y = QtWidgets.QSpinBox()
        self.spin_y.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_y.setMinimum(0)
        self.spin_y.setMaximum(2000)
        self.spin_y.setValue(int(self.obstacle_entity.transform.translation().y()))
        self.spin_y.valueChanged.connect(self.obstacle_entity.setYTranslation)
        layout.addWidget(label_y, row, 0)
        layout.addWidget(self.spin_y, row, 1)
        row += 1

        label_rotation = QtWidgets.QLabel("Rotation")
        self.spin_rotation = QtWidgets.QSpinBox()
        self.spin_rotation.setSuffix("°")
        self.spin_rotation.setMinimum(-180)
        self.spin_rotation.setMaximum(180)
        self.spin_rotation.setValue(int(self.obstacle_entity.transform.rotationZ()))
        self.spin_rotation.valueChanged.connect(self.obstacle_entity.transform.setRotationZ)
        layout.addWidget(label_rotation, row, 0)
        layout.addWidget(self.spin_rotation, row, 1)
        row += 1

        label_width = QtWidgets.QLabel("Width")
        self.spin_width = QtWidgets.QSpinBox()
        self.spin_width.setMaximum(2000)
        self.spin_width.setSingleStep(10)
        self.spin_width.setValue(int(self.obstacle_entity.mesh.xExtent()))
        self.spin_width.valueChanged.connect(self.obstacle_entity.mesh.setXExtent)
        layout.addWidget(label_width, row, 0)
        layout.addWidget(self.spin_width, row, 1)
        row += 1

        label_length = QtWidgets.QLabel("Length")
        self.spin_length = QtWidgets.QSpinBox()
        self.spin_length.setMaximum(2000)
        self.spin_length.setSingleStep(10)
        self.spin_length.setValue(int(self.obstacle_entity.mesh.yExtent()))
        self.spin_length.valueChanged.connect(self.obstacle_entity.mesh.setYExtent)
        layout.addWidget(label_length, row, 0)
        layout.addWidget(self.spin_length, row, 1)
        row += 1

        label_height = QtWidgets.QLabel("Height")
        self.spin_height = QtWidgets.QSpinBox()
        self.spin_height.setMaximum(1000)
        self.spin_height.setSingleStep(10)
        self.spin_height.setValue(int(self.obstacle_entity.mesh.zExtent()))
        self.spin_height.valueChanged.connect(self.obstacle_entity.mesh.setZExtent)
        layout.addWidget(label_height, row, 0)
        layout.addWidget(self.spin_height, row, 1)
        row += 1

    @classmethod
    def set_saved_geometry(cls, geometry: QtCore.QRect):
        """
        Class method.

        Save the position of the last displayed property window.

        Arguments:
            geometry: The position to save
        """
        cls.saved_geometry = geometry

    @classmethod
    def set_active_properties(cls, properties: "ObstacleProperties"):
        """
        Class method.

        Set the current property window displayed.

        Arguments:
            properties: The current property
        """
        cls.active_properties = properties

    def restore_saved_geometry(self):
        """
        Reuse the position of the last displayed property window for the current window.
        """
        if ObstacleProperties.saved_geometry:
            self.setGeometry(ObstacleProperties.saved_geometry)

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Close the property windows.

        Arguments:
            event: The close event (unused)
        """
        ObstacleProperties.set_saved_geometry(self.geometry())
        ObstacleProperties.set_active_properties(None)
        event.accept()

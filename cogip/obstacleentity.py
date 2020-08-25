from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.QtCore import Slot as qtSlot

from cogip.sensor import Sensor
from cogip import models


class ObstacleEntity(Qt3DCore.QEntity):

    def __init__(
            self,
            parent_widget: QtWidgets.QWidget,
            x: int = 0,
            y: int = 1000,
            rotation: int = 0,
            length: int = 200,
            width: int = 200,
            height: int = 600):

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

        self.picker = Qt3DRender.QObjectPicker(self)
        self.picker.setDragEnabled(True)
        self.picker.clicked.connect(self.clicked_obstacle)
        self.addComponent(self.picker)

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
        translation = self.transform.translation()
        translation.setZ(zExtent/2)
        self.transform.setTranslation(translation)

    @qtSlot(int)
    def setXTranslation(self, x: int):
        translation = self.transform.translation()
        translation.setX(float(x))
        self.transform.setTranslation(translation)

    @qtSlot(int)
    def setYTranslation(self, y: int):
        translation = self.transform.translation()
        translation.setY(float(y))
        self.transform.setTranslation(translation)

    @qtSlot(Qt3DRender.QPickEvent)
    def clicked_obstacle(self, pick: Qt3DRender.QPickEvent):
        if ObstacleProperties.active_properties:
            ObstacleProperties.active_properties.close()
        self.properties.restore_saved_geometry()
        self.properties.show()
        self.properties.raise_()
        self.properties.activateWindow()
        ObstacleProperties.set_active_properties(self.properties)

    def get_model(self) -> models.Obstacle:
        return models.Obstacle(
            x=self.transform.translation().x(),
            y=self.transform.translation().y(),
            rotation=self.transform.rotationZ(),
            length=self.mesh.yExtent(),
            width=self.mesh.xExtent(),
            height=self.mesh.zExtent()
        )


class ObstacleProperties(QtWidgets.QDialog):

    saved_geometry = None
    active_properties = None

    def __init__(self, parent: QtWidgets.QWidget, obstacle_entity: ObstacleEntity):
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
        cls.saved_geometry = geometry

    @classmethod
    def set_active_properties(cls, properties):
        cls.active_properties = properties

    def restore_saved_geometry(self):
        if ObstacleProperties.saved_geometry:
            self.setGeometry(ObstacleProperties.saved_geometry)

    def closeEvent(self, event: QtGui.QCloseEvent):
        ObstacleProperties.set_saved_geometry(self.geometry())
        ObstacleProperties.set_active_properties(None)
        event.accept()

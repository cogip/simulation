from typing import Dict, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from cogip.models import models
from cogip.models.models import CakeLayerID, CakeLayerKind, CakeLayerPos, CherryID, CherryLocation


# Map converting color enum to Qt color
pos_map: Dict[CakeLayerPos, int] = {
    CakeLayerPos.BOTTOM: 0,
    CakeLayerPos.MIDDLE: 20,
    CakeLayerPos.TOP: 40
}

kind_map: Dict[CakeLayerKind, QtGui.QColor] = {
    CakeLayerKind.ICING: QtGui.QColor.fromRgb(195, 0, 195, 255),
    CakeLayerKind.CREAM: QtGui.QColor.fromRgb(255, 191, 0, 255),
    CakeLayerKind.SPONGE: QtGui.QColor.fromRgb(46, 15, 23, 255)
}

face_map: Dict[CakeLayerKind, str] = {
    CakeLayerKind.ICING:  "cake_layer_icing.png",
    CakeLayerKind.CREAM:  "cake_layer_cream.png",
    CakeLayerKind.SPONGE: "cake_layer_sponge.png"
}

# Default position and properties of all cake layers
default_cake_layers: Dict[CakeLayerID, Tuple[float, float, CakeLayerKind, CakeLayerPos]] = {
    # Cake Layer ID:                       (x,                  y,               kind,                position)

    # Green Front quarter
    CakeLayerID.GREEN_FRONT_ICING_BOTTOM:  (450+125,            1000-225,        CakeLayerKind.ICING, CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_FRONT_ICING_MIDDLE:  (450+125,            1000-225,        CakeLayerKind.ICING, CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_FRONT_ICING_TOP:     (450+125,            1000-225,        CakeLayerKind.ICING, CakeLayerPos.TOP),

    CakeLayerID.GREEN_FRONT_CREAM_BOTTOM:  (450+125+200,        1000-225,        CakeLayerKind.CREAM, CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_FRONT_CREAM_MIDDLE:  (450+125+200,        1000-225,        CakeLayerKind.CREAM, CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_FRONT_CREAM_TOP:     (450+125+200,        1000-225,        CakeLayerKind.CREAM, CakeLayerPos.TOP),

    CakeLayerID.GREEN_FRONT_SPONGE_BOTTOM: (1125,               1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_FRONT_SPONGE_MIDDLE: (1125,               1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_FRONT_SPONGE_TOP:    (1125,               1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.TOP),

    # Green Back quarter
    CakeLayerID.GREEN_BACK_SPONGE_BOTTOM:  (3000-1125,          1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_BACK_SPONGE_MIDDLE:  (3000-1125,          1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_BACK_SPONGE_TOP:     (3000-1125,          1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.TOP),

    CakeLayerID.GREEN_BACK_CREAM_BOTTOM:   (3000-(450+125+200), 1000-225,        CakeLayerKind.CREAM,  CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_BACK_CREAM_MIDDLE:   (3000-(450+125+200), 1000-225,        CakeLayerKind.CREAM,  CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_BACK_CREAM_TOP:      (3000-(450+125+200), 1000-225,        CakeLayerKind.CREAM,  CakeLayerPos.TOP),

    CakeLayerID.GREEN_BACK_ICING_BOTTOM:   (3000-(450+125),     1000-225,        CakeLayerKind.ICING,  CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_BACK_ICING_MIDDLE:   (3000-(450+125),     1000-225,        CakeLayerKind.ICING,  CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_BACK_ICING_TOP:      (3000-(450+125),     1000-225,        CakeLayerKind.ICING,  CakeLayerPos.TOP),

    # Blue Front quarter
    CakeLayerID.BLUE_FRONT_ICING_BOTTOM:   (450+125,            -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_FRONT_ICING_MIDDLE:   (450+125,            -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_FRONT_ICING_TOP:      (450+125,            -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.TOP),

    CakeLayerID.BLUE_FRONT_CREAM_BOTTOM:   (450+125+200,        -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_FRONT_CREAM_MIDDLE:   (450+125+200,        -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_FRONT_CREAM_TOP:      (450+125+200,        -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.TOP),

    CakeLayerID.BLUE_FRONT_SPONGE_BOTTOM:  (1125,               -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_FRONT_SPONGE_MIDDLE:  (1125,               -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_FRONT_SPONGE_TOP:     (1125,               -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.TOP),

    # Blue Back quarter
    CakeLayerID.BLUE_BACK_SPONGE_BOTTOM:   (3000-1125,          -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_BACK_SPONGE_MIDDLE:   (3000-1125,          -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_BACK_SPONGE_TOP:      (3000-1125,          -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.TOP),

    CakeLayerID.BLUE_BACK_CREAM_BOTTOM:    (3000-(450+125+200), -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_BACK_CREAM_MIDDLE:    (3000-(450+125+200), -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_BACK_CREAM_TOP:       (3000-(450+125+200), -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.TOP),

    CakeLayerID.BLUE_BACK_ICING_BOTTOM:    (3000-(450+125),     -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_BACK_ICING_MIDDLE:    (3000-(450+125),     -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_BACK_ICING_TOP:       (3000-(450+125),     -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.TOP)
}


class CakeLayerEntity(Qt3DCore.QEntity):
    """
    A cake layer on the table.

    When selected with a mouse click, a property window is displayed
    to modify the cake layer properties.

    The cake layer can also be moved using the mouse.

    Attributes:
        enable_controller: Qt signal used to disable the camera controller
            when moving the cake layer using the mouse
    """
    enable_controller = qtSignal(bool)

    def __init__(self, id: CakeLayerID, parent: Qt3DCore.QEntity, parent_widget: QtWidgets.QWidget):
        """
        Class constructor.
        """
        super().__init__(parent)
        self._id: CakeLayerID = id
        self._x: float
        self._y: float
        self._kind: CakeLayerKind
        self._pos: CakeLayerPos

        (self._x, self._y, self._kind, self._pos) = default_cake_layers[id]

        self._picker = Qt3DRender.QObjectPicker()
        self._picker.setDragEnabled(True)
        self._picker.pressed.connect(self.pressed)
        self._picker.released.connect(self.released)
        self._picker.moved.connect(self.moved)
        self.addComponent(self._picker)

        self._moving = False

        mesh = Qt3DExtras.QCylinderMesh(self)
        mesh.setLength(20)
        mesh.setRadius(60)

        self._transform = Qt3DCore.QTransform(self)
        self._transform.setRotationX(90)

        self._material = Qt3DExtras.QDiffuseSpecularMaterial(self)
        self._material.setShininess(1.0)
        self._material.setAlphaBlendingEnabled(True)

        self.addComponent(mesh)
        self.addComponent(self._transform)
        self.addComponent(self._material)

        self._face_entity = Qt3DCore.QEntity(self)

        face_mesh = Qt3DExtras.QPlaneMesh(self._face_entity)
        face_mesh.setHeight(120)
        face_mesh.setWidth(120)
        self._face_entity.addComponent(face_mesh)

        face_material = Qt3DExtras.QTextureMaterial(self._face_entity)
        face_texture = Qt3DRender.QTexture2D(face_material)
        self._face_texture_image = Qt3DRender.QTextureImage(face_texture)
        self._face_texture_image.setMirrored(False)
        face_texture.addTextureImage(self._face_texture_image)
        face_material.setTexture(face_texture)
        face_material.setAlphaBlendingEnabled(True)
        self._face_entity.addComponent(face_material)

        face_transform = Qt3DCore.QTransform(self._face_entity)
        face_transform.setTranslation(QtGui.QVector3D(0, 10, 0))
        self._face_entity.addComponent(face_transform)

        self.set_kind(self._kind)
        self.set_pos(self._x, self._y)

        # Create properties dialog
        self._properties = CakeLayerProperties(parent_widget, self)

    @property
    def kind(self) -> CakeLayerKind:
        """
        Get cake layer kind
        """
        return self._kind

    @qtSlot(CakeLayerKind)
    def set_kind(self, kind: CakeLayerKind) -> None:
        """
        Qt Slot

        Update cake layer kind
        """
        self._kind = kind
        self._material.setDiffuse(kind_map[kind])
        self._material.setAmbient(kind_map[kind])
        self._face_texture_image.setSource(QtCore.QUrl(f"file:assets/{face_map[self._kind]}"))

    @qtSlot(str)
    def set_kind_text(self, kind: str) -> None:
        """
        Qt Slot

        Update cake layer kind from kind string
        """
        self.set_kind(CakeLayerKind[kind])

    @property
    def pos(self) -> CakeLayerPos:
        """
        Get cake layer position
        """
        return self._pos

    def set_pos(self, x: float, y: float) -> None:
        """
        Update position
        """
        self._x = x
        self._y = y

        self._transform.setTranslation(QtGui.QVector3D(
            self._x,
            self._y,
            pos_map[self._pos] + 10
        ))

    @qtSlot(str)
    def set_pos_text(self, pos: str) -> None:
        """
        Qt Slot

        Update cake layer position from position string
        """
        self.set_pos(CakeLayerPos[pos])
        self.set_pos(self._x, self._y)

    @qtSlot(int)
    def set_x(self, x: int):
        """
        Qt Slot

        Set the X position.
        """
        self.set_pos(float(x), self._y)

    @qtSlot(int)
    def set_y(self, y: int):
        """
        Qt Slot

        Set the Y position.
        """
        self.set_pos(self._x, float(y))

    @qtSlot(Qt3DRender.QPickEvent)
    def pressed(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```pressed``` mouse event on the cake layer.

        Emit a signal to disable the camera controller before moving the cake layer.
        """
        self.enable_controller.emit(False)

    @qtSlot(Qt3DRender.QPickEvent)
    def released(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```released``` mouse event on the cake layer.

        If this event occurs juste after a ```pressed``` event, it is only a mouse click,
        so display the property window.

        Emit a signal to re-enable the camera controller after moving the cake layer.
        """
        if not self._moving:
            if CakeLayerProperties.active_properties:
                CakeLayerProperties.active_properties.close()
            self._properties.show()
            self._properties.raise_()
            self._properties.activateWindow()
            CakeLayerProperties.set_active_properties(self._properties)
        self._moving = False
        self.enable_controller.emit(True)

    @qtSlot(Qt3DRender.QPickEvent)
    def moved(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```moved``` mouse event on the cake layer.

        Just record that the cake layer is moving, the translation is computed
        in the [GameView][cogip.widgets.gameview.GameView] object.
        """
        self._moving = True

    def get_model(self) -> models.CakeLayer:
        """
        Returns the [CakeLayer][cogip.models.models.CakeLayer] model.
        Used to save the cake layers list.

        Returns:
            The cake layer model
        """
        return models.CakeLayer(
            id=self._id,
            x=self._x,
            y=self._y,
            kind=self._kind,
            pos=self._pos
        )

    def update_from_model(self, model: models.CakeLayer) -> None:
        """
        Update cake layer properties from a cake layer model
        """
        self.set_pos(model.x, model.y)
        self.set_kind(model.kind)

    @qtSlot(QtGui.QVector3D)
    def new_move_delta(self, delta: QtGui.QVector3D):
        """
        Qt Slot

        Update the cake layer position.

        Arguments:
            delta: The difference between current and new position
        """
        if not delta:
            self._moving = False
        elif self._moving:
            new_translation = self._transform.translation() + delta
            self._transform.setTranslation(new_translation)
            self._properties.spin_x.setValue(new_translation.x())
            self._properties.spin_y.setValue(new_translation.y())


class CakeLayerProperties(QtWidgets.QDialog):
    """
    The property window.

    Each cake layer has its own property window.

    Attributes:
        active_properties: The current property window displayed.
    """
    active_properties: "CakeLayerProperties" = None

    def __init__(self, parent: QtWidgets.QWidget, cake_layer_entity: CakeLayerEntity):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
            cake_layer_entity: The related cake layer entity
        """
        super().__init__(parent)

        self.cake_layer_entity = cake_layer_entity
        self.setWindowTitle("Cake Layer Properties")
        self.setModal(False)
        self.setMinimumWidth(self.fontMetrics().horizontalAdvance(self.windowTitle()))

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        row = 0

        label_x = QtWidgets.QLabel("X")
        self.spin_x = QtWidgets.QSpinBox()
        self.spin_x.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_x.setMinimum(0)
        self.spin_x.setMaximum(3000)
        self.spin_x.setValue(int(self.cake_layer_entity._x))
        self.spin_x.valueChanged.connect(self.cake_layer_entity.set_x)
        layout.addWidget(label_x, row, 0)
        layout.addWidget(self.spin_x, row, 1)
        row += 1

        label_y = QtWidgets.QLabel("Y")
        self.spin_y = QtWidgets.QSpinBox()
        self.spin_y.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_y.setMinimum(-1500)
        self.spin_y.setMaximum(1500)
        self.spin_y.setValue(int(self.cake_layer_entity._y))
        self.spin_y.valueChanged.connect(self.cake_layer_entity.set_y)
        layout.addWidget(label_y, row, 0)
        layout.addWidget(self.spin_y, row, 1)
        row += 1

        label_kind = QtWidgets.QLabel("Kind")
        self.combo_kind = QtWidgets.QComboBox()
        for kind in CakeLayerKind:
            self.combo_kind.addItem(kind.name, kind.value)
        self.combo_kind.setCurrentText(self.cake_layer_entity.kind.name)
        self.combo_kind.currentTextChanged.connect(self.cake_layer_entity.set_kind_text)
        layout.addWidget(label_kind, row, 0)
        layout.addWidget(self.combo_kind, row, 1)
        row += 1

        label_pos = QtWidgets.QLabel("Position")
        self.combo_pos = QtWidgets.QComboBox()
        for pos in CakeLayerPos:
            self.combo_pos.addItem(pos.name, pos.value)
        self.combo_pos.setCurrentText(self.cake_layer_entity.pos.name)
        self.combo_pos.currentTextChanged.connect(self.cake_layer_entity.set_pos_text)
        layout.addWidget(label_pos, row, 0)
        layout.addWidget(self.combo_pos, row, 1)
        row += 1

        self.readSettings()

    @classmethod
    def set_active_properties(cls, properties: "CakeLayerProperties"):
        """
        Class method.

        Set the current property window displayed.

        Arguments:
            properties: The current property
        """
        cls.active_properties = properties

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Close the property windows.

        Arguments:
            event: The close event (unused)
        """
        CakeLayerProperties.set_active_properties(None)

        settings = QtCore.QSettings("COGIP", "monitor")
        settings.setValue("cake_layer_dialog/geometry", self.saveGeometry())

        super().closeEvent(event)

    def readSettings(self):
        settings = QtCore.QSettings("COGIP", "monitor")
        self.restoreGeometry(settings.value("cake_layer_dialog/geometry"))


cherry_location_map: Dict[CherryLocation, int] = {
    CherryLocation.BOTTOM: 20,
    CherryLocation.MIDDLE: 40,
    CherryLocation.TOP: 60,
    CherryLocation.RACK: 20
}


# Default position and properties of all cherries
default_cherries: Dict[CherryID, Tuple[float, float, CherryLocation]] = {
    # Cherry ID:       (x,                y,        position)
    CherryID.FRONT_1:  (15,               0,        CherryLocation.RACK),
    CherryID.FRONT_2:  (15+30,            0,        CherryLocation.RACK),
    CherryID.FRONT_3:  (15+30*2,          0,        CherryLocation.RACK),
    CherryID.FRONT_4:  (15+30*3,          0,        CherryLocation.RACK),
    CherryID.FRONT_5:  (15+30*4,          0,        CherryLocation.RACK),
    CherryID.FRONT_6:  (15+30*5,          0,        CherryLocation.RACK),
    CherryID.FRONT_7:  (15+30*6,          0,        CherryLocation.RACK),
    CherryID.FRONT_8:  (15+30*7,          0,        CherryLocation.RACK),
    CherryID.FRONT_9:  (15+30*8,          0,        CherryLocation.RACK),
    CherryID.FRONT_10: (15+30*9,          0,        CherryLocation.RACK),

    CherryID.BACK_1:   (3000-15,          0,        CherryLocation.RACK),
    CherryID.BACK_2:   (3000-15-30,       0,        CherryLocation.RACK),
    CherryID.BACK_3:   (3000-15-30*2,     0,        CherryLocation.RACK),
    CherryID.BACK_4:   (3000-15-30*3,     0,        CherryLocation.RACK),
    CherryID.BACK_5:   (3000-15-30*4,     0,        CherryLocation.RACK),
    CherryID.BACK_6:   (3000-15-30*5,     0,        CherryLocation.RACK),
    CherryID.BACK_7:   (3000-15-30*6,     0,        CherryLocation.RACK),
    CherryID.BACK_8:   (3000-15-30*7,     0,        CherryLocation.RACK),
    CherryID.BACK_9:   (3000-15-30*8,     0,        CherryLocation.RACK),
    CherryID.BACK_10:  (3000-15-30*9,     0,        CherryLocation.RACK),

    CherryID.GREEN_1:  (1500-150+15,      1000-15,  CherryLocation.RACK),
    CherryID.GREEN_2:  (1500-150+15+30,   1000-15,  CherryLocation.RACK),
    CherryID.GREEN_3:  (1500-150+15+30*2, 1000-15,  CherryLocation.RACK),
    CherryID.GREEN_4:  (1500-150+15+30*3, 1000-15,  CherryLocation.RACK),
    CherryID.GREEN_5:  (1500-150+15+30*4, 1000-15,  CherryLocation.RACK),
    CherryID.GREEN_6:  (1500-150+15+30*5, 1000-15,  CherryLocation.RACK),
    CherryID.GREEN_7:  (1500-150+15+30*6, 1000-15,  CherryLocation.RACK),
    CherryID.GREEN_8:  (1500-150+15+30*7, 1000-15,  CherryLocation.RACK),
    CherryID.GREEN_9:  (1500-150+15+30*8, 1000-15,  CherryLocation.RACK),
    CherryID.GREEN_10: (1500-150+15+30*9, 1000-15,  CherryLocation.RACK),

    CherryID.BLUE_1:   (1500-150+15,      -1000+15, CherryLocation.RACK),
    CherryID.BLUE_2:   (1500-150+15+30,   -1000+15, CherryLocation.RACK),
    CherryID.BLUE_3:   (1500-150+15+30*2, -1000+15, CherryLocation.RACK),
    CherryID.BLUE_4:   (1500-150+15+30*3, -1000+15, CherryLocation.RACK),
    CherryID.BLUE_5:   (1500-150+15+30*4, -1000+15, CherryLocation.RACK),
    CherryID.BLUE_6:   (1500-150+15+30*5, -1000+15, CherryLocation.RACK),
    CherryID.BLUE_7:   (1500-150+15+30*6, -1000+15, CherryLocation.RACK),
    CherryID.BLUE_8:   (1500-150+15+30*7, -1000+15, CherryLocation.RACK),
    CherryID.BLUE_9:   (1500-150+15+30*8, -1000+15, CherryLocation.RACK),
    CherryID.BLUE_10:  (1500-150+15+30*9, -1000+15, CherryLocation.RACK),
}


class CherryEntity(Qt3DCore.QEntity):
    """
    A cherry on the table.
    """
    def __init__(self, id: CherryID, parent: Qt3DCore.QEntity, parent_widget: QtWidgets.QWidget):
        """
        Class constructor.
        """
        super().__init__(parent)
        self._id: CherryID = id
        self._x: float
        self._y: float
        self._location: CherryLocation

        mesh = Qt3DExtras.QSphereMesh(self)
        mesh.setRadius(10)

        self._transform = Qt3DCore.QTransform(self)

        self._material = Qt3DExtras.QDiffuseSpecularMaterial(self)
        self._material.setShininess(1.0)
        self._material.setAlphaBlendingEnabled(True)
        self._material.setDiffuse(QtGui.QColor(QtCore.Qt.red))
        self._material.setAmbient(QtGui.QColor(QtCore.Qt.red))

        self.addComponent(mesh)
        self.addComponent(self._transform)
        self.addComponent(self._material)

        (self.x, self.y, self.location) = default_cherries[id]

    @property
    def location(self) -> CherryLocation:
        """
        Get cherry location
        """
        return self._pos

    @location.setter
    def location(self, location: CherryLocation) -> None:
        """
        Update cherry location
        """
        self._location = location

        loc = cherry_location_map.get(self._location)
        if loc:
            self.setEnabled(True)
            self._transform.setTranslation(QtGui.QVector3D(
                self._x,
                self._y,
                loc
            ))
        else:
            self.setEnabled(False)

    @property
    def x(self) -> int:
        """
        Get X coordinate.
        """
        return self._x

    @x.setter
    def x(self, x: float):
        """
        Set X coordinate.
        """
        self._x = float(x)

    @property
    def y(self) -> int:
        """
        Get Y coordinate.
        """
        return self._y

    @y.setter
    def y(self, y: float):
        """
        Set Y coordinate.
        """
        self._y = float(y)


def create_cake_layers(parent: Qt3DCore.QEntity, parent_widget: QtWidgets.QWidget) -> Dict[CakeLayerID, CakeLayerEntity]:
    """
    Add default cake layers on the table

    Arguments:
            parent: The parent entity
            parent_widget: The parent widget
    """
    cake_layers = {}

    for cake_layer_id in default_cake_layers.keys():
        cake_layers[cake_layer_id] = CakeLayerEntity(cake_layer_id, parent, parent_widget)

    return cake_layers


def create_cherries(parent: Qt3DCore.QEntity, parent_widget: QtWidgets.QWidget) -> Dict[CherryID, CherryEntity]:
    """
    Add default cherries on the table

    Arguments:
            parent: The parent entity
            parent_widget: The parent widget
    """
    cherries = {}

    for cherry_id in default_cherries.keys():
        cherries[cherry_id] = CherryEntity(cherry_id, parent, parent_widget)

    return cherries

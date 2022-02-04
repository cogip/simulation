from typing import Dict, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import Signal as qtSignal
from PySide6.QtCore import Slot as qtSlot

from cogip.models import models
from cogip.models.models import SampleID, SampleColor


# Map converting color enum to Qt color
color_map: Dict[SampleColor, QtCore.Qt.GlobalColor] = {
    SampleColor.ROCK: QtCore.Qt.gray,
    SampleColor.RED: QtCore.Qt.red,
    SampleColor.GREEN: QtCore.Qt.green,
    SampleColor.BLUE: QtCore.Qt.blue
}


# Default positionand properties of all samples
default_samples: Dict[SampleID, Tuple[SampleColor, bool, bool, float, float, float, float, float, float]] = {
    # Sample ID:                    (     color,        hidden, known, angle_x, angle_y, angle_z,    pos_x,   pos_y, pos_z)
    SampleID.YELLOW_TABLE_FIXED_B:  (SampleColor.BLUE,    True,  True,       0,       0,       0,      600,     555,     0),
    SampleID.YELLOW_TABLE_FIXED_G:  (SampleColor.GREEN,   True,  True,       0,       0,       0,      670,     675,     0),
    SampleID.YELLOW_TABLE_FIXED_R:  (SampleColor.RED,     True,  True,       0,       0,       0,      600,     795,     0),
    SampleID.YELLOW_TABLE_RANDOM_1: (SampleColor.BLUE,   False, False,       0,       0,       0,   607.70, 1292.30,     0),
    SampleID.YELLOW_TABLE_RANDOM_2: (SampleColor.GREEN,  False, False,       0,       0,       0,   455.74, 1329.13,     0),
    SampleID.YELLOW_TABLE_RANDOM_3: (SampleColor.RED,    False, False,       0,       0,       0,      550,    1450,     0),
    SampleID.YELLOW_SHED_R:         (SampleColor.RED,     True,  True,       0,       0,    -135,  1188.43, 1879.35,    70),
    SampleID.YELLOW_SHED_B:         (SampleColor.BLUE,    True,  True,       0,       0,      45,  1379.35, 1688.43,    70),
    SampleID.YELLOW_OUTSIDE_G:      (SampleColor.GREEN,   True,  True,       0,       0,       0,  1564.95,     300,    70),
    SampleID.YELLOW_RACK_SIDE_R:    (SampleColor.RED,     True,  True,       0,     -60,       0,  1494.98,    1250, 59.05),
    SampleID.YELLOW_RACK_SIDE_G:    (SampleColor.GREEN,   True,  True,       0,     -60,       0,  1478.48,    1250, 59.05),
    SampleID.YELLOW_RACK_SIDE_B:    (SampleColor.BLUE,    True,  True,       0,     -60,       0,  1461.98,    1250, 59.05),
    SampleID.YELLOW_RACK_TOP_R:     (SampleColor.RED,     True,  True,     -60,       0,       0,      150,    5.02, 59.05),
    SampleID.YELLOW_RACK_TOP_G:     (SampleColor.GREEN,   True,  True,     -60,       0,       0,      150,   21.52, 59.05),
    SampleID.YELLOW_RACK_TOP_B:     (SampleColor.BLUE,    True,  True,     -60,       0,       0,      150,   38.05, 59.05),
    SampleID.PURPLE_TABLE_FIXED_B:  (SampleColor.BLUE,    True,  True,       0,       0,       0,     -600,     555,     0),
    SampleID.PURPLE_TABLE_FIXED_G:  (SampleColor.GREEN,   True,  True,       0,       0,       0,     -670,     675,     0),
    SampleID.PURPLE_TABLE_FIXED_R:  (SampleColor.RED,     True,  True,       0,       0,       0,     -600,     795,     0),
    SampleID.PURPLE_TABLE_RANDOM_1: (SampleColor.BLUE,   False, False,       0,       0,       0,  -613.92, 1288.38,     0),
    SampleID.PURPLE_TABLE_RANDOM_2: (SampleColor.GREEN,  False, False,       0,       0,       0,  -454.32, 1366.48,     0),
    SampleID.PURPLE_TABLE_RANDOM_3: (SampleColor.RED,    False, False,       0,       0,       0,  -585.06, 1444.28,     0),
    SampleID.PURPLE_SHED_B:         (SampleColor.BLUE,    True,  True,       0,       0,     -45, -1379.35, 1688.43,    70),
    SampleID.PURPLE_SHED_R:         (SampleColor.RED,     True,  True,       0,       0,     135, -1188.43, 1879.35,    70),
    SampleID.PURPLE_OUTSIDE_G:      (SampleColor.GREEN,   True,  True,       0,       0,       0, -1564.95,     300,    70),
    SampleID.PURPLE_RACK_SIDE_R:    (SampleColor.RED,     True,  True,       0,      60,       0, -1494.98,    1250, 59.05),
    SampleID.PURPLE_RACK_SIDE_G:    (SampleColor.GREEN,   True,  True,       0,      60,       0, -1478.48,    1250, 59.05),
    SampleID.PURPLE_RACK_SIDE_B:    (SampleColor.BLUE,    True,  True,       0,      60,       0, -1461.98,    1250, 59.05),
    SampleID.PURPLE_RACK_TOP_R:     (SampleColor.RED,     True,  True,     -60,       0,       0,     -150,    5.02, 59.05),
    SampleID.PURPLE_RACK_TOP_G:     (SampleColor.GREEN,   True,  True,     -60,       0,       0,     -150,   21.52, 59.05),
    SampleID.PURPLE_RACK_TOP_B:     (SampleColor.BLUE,    True,  True,     -60,       0,       0,     -150,   38.02, 59.05)
}


class SampleEntity(Qt3DCore.QEntity):
    """
    A sample on the table.

    When selected with a mouse click, a property window is displayed
    to modify the sample properties.

    The sample can also be moved using the mouse.

    Attributes:
        enable_controller: Qt signal used to disable the camera controller
            when moving the sample using the mouse
    """
    enable_controller = qtSignal(bool)

    def __init__(self, id: SampleID, parent: Qt3DCore.QEntity, parent_widget: QtWidgets.QWidget):
        """
        Class constructor.
        """
        super().__init__(parent)
        self._id: SampleID = id
        self._pos_x: float
        self._pos_y: float
        self._pos_z: float
        self._angle_x: float
        self._angle_y: float
        self._angle_z: float
        self._color: SampleColor
        self._hidden: bool
        self._known: bool

        (self._color, self._hidden, self._known,
         self._angle_x, self._angle_y, self._angle_z,
         self._pos_x, self._pos_y, self._pos_z) = default_samples[id]

        self._picker = Qt3DRender.QObjectPicker()
        self._picker.setDragEnabled(True)
        self._picker.pressed.connect(self.pressed)
        self._picker.released.connect(self.released)
        self._picker.moved.connect(self.moved)
        self.addComponent(self._picker)

        self._moving = False

        mesh = Qt3DRender.QMesh(self)
        mesh.setSource(QtCore.QUrl("file:assets/sample.obj"))

        self._transform = Qt3DCore.QTransform(self)

        self._material = Qt3DExtras.QDiffuseSpecularMaterial(self)
        self._material.setShininess(1.0)
        self._material.setAlphaBlendingEnabled(True)

        self.addComponent(mesh)
        self.addComponent(self._transform)
        self.addComponent(self._material)

        self._face_entity = Qt3DCore.QEntity(self)

        face_mesh = Qt3DExtras.QPlaneMesh(self._face_entity)
        face_mesh.setHeight(150)
        face_mesh.setWidth(130)
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
        face_transform.setRotationX(-90)
        face_transform.setRotationY(180)
        face_transform.setTranslation(QtGui.QVector3D(0, 0, 15))
        self._face_entity.addComponent(face_transform)

        self.set_color(self._color)
        self.set_pos(self._pos_x, self._pos_y, self._pos_z)
        self.set_angle(self._angle_x, self._angle_y, self._angle_z)

        # Create properties dialog
        self._properties = SampleProperties(parent_widget, self)

    @property
    def hidden(self) -> bool:
        """
        Get hidden property
        """
        return self._hidden

    @qtSlot(bool)
    def set_hidden(self, hidden: bool):
        """
        Set hidden property
        """
        self._hidden = hidden
        self.set_color(self._color)

    @property
    def known(self) -> bool:
        """
        Get known property
        """
        return self._known

    @qtSlot(bool)
    def set_known(self, known: bool):
        """
        Set known property
        """
        self._known = known
        self.set_color(self._color)

    @property
    def color(self) -> SampleColor:
        """
        Get sample color
        """
        return self._color

    def set_pos(self, x: float, y: float, z: float) -> None:
        """
        Update position
        """
        self._pos_x = x
        self._pos_y = y
        self._pos_z = z

        self._transform.setTranslation(QtGui.QVector3D(
            self._pos_x,
            self._pos_y,
            self._pos_z
        ))

    def set_angle(self, x: float, y: float, z: float) -> None:
        """
        Update angles
        """
        self._angle_x = x
        self._angle_y = y
        self._angle_z = z
        self._transform.setRotationX(x)
        self._transform.setRotationY(y)
        self._transform.setRotationZ(z)

    @qtSlot(SampleColor)
    def set_color(self, color: SampleColor) -> None:
        """
        Qt Slot

        Update sample color and face color
        """
        self._color = color

        if self._known:
            self._material.setDiffuse(QtGui.QColor(color_map[color]))
            self._material.setAmbient(QtGui.QColor(color_map[color]))
        else:
            self._material.setDiffuse(QtGui.QColor(color_map[SampleColor.ROCK]))
            self._material.setAmbient(QtGui.QColor(color_map[SampleColor.ROCK]))

        if self._hidden:
            self._face_texture_image.setSource(QtCore.QUrl("file:assets/sample-rock.png"))
        elif color == SampleColor.GREEN:
            self._face_texture_image.setSource(QtCore.QUrl("file:assets/sample-green.png"))
        elif color == SampleColor.RED:
            self._face_texture_image.setSource(QtCore.QUrl("file:assets/sample-red.png"))
        elif color == SampleColor.BLUE:
            self._face_texture_image.setSource(QtCore.QUrl("file:assets/sample-blue.png"))

    @qtSlot(str)
    def set_color_text(self, color: str) -> None:
        """
        Qt Slot

        Update sample color and face color from color string
        """
        self.set_color(SampleColor[color])

    @qtSlot(int)
    def set_pos_x(self, x: int):
        """
        Qt Slot

        Set the X position.
        """
        self.set_pos(float(x), self._pos_y, self._pos_z)

    @qtSlot(int)
    def set_pos_y(self, y: int):
        """
        Qt Slot

        Set the Y position.
        """
        self.set_pos(self._pos_x, float(y), self._pos_z)

    @qtSlot(int)
    def set_pos_z(self, z: int):
        """
        Qt Slot

        Set the Z position.
        """
        self.set_pos(self._pos_x, self._pos_y, float(z))

    @qtSlot(int)
    def set_angle_x(self, x: int):
        """
        Qt Slot

        Set the X angle.
        """
        self.set_angle(float(x), self._angle_y, self._angle_z)

    @qtSlot(int)
    def set_angle_y(self, y: int):
        """
        Qt Slot

        Set the Y angle.
        """
        self.set_angle(self._angle_x, float(y), self._angle_z)

    @qtSlot(int)
    def set_angle_z(self, z: int):
        """
        Qt Slot

        Set the Z angle.
        """
        self.set_angle(self._angle_x, self._angle_y, float(z))

    @qtSlot(Qt3DRender.QPickEvent)
    def pressed(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```pressed``` mouse event on the sample.

        Emit a signal to disable the camera controller before moving the sample.
        """
        self.enable_controller.emit(False)

    @qtSlot(Qt3DRender.QPickEvent)
    def released(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```released``` mouse event on the sample.

        If this event occurs juste after a ```pressed``` event, it is only a mouse click,
        so display the property window.

        Emit a signal to re-enable the camera controller after moving the sample.
        """
        if not self._moving:
            if SampleProperties.active_properties:
                SampleProperties.active_properties.close()
            self._properties.restore_saved_geometry()
            self._properties.show()
            self._properties.raise_()
            self._properties.activateWindow()
            SampleProperties.set_active_properties(self._properties)
        self._moving = False
        self.enable_controller.emit(True)

    @qtSlot(Qt3DRender.QPickEvent)
    def moved(self, pick: Qt3DRender.QPickEvent):
        """
        Qt Slot

        Slot called on a ```moved``` mouse event on the sample.

        Just record that the sample is moving, the translation is computed
        in the [GameView][cogip.widgets.gameview.GameView] object.
        """
        self._moving = True

    def get_model(self) -> models.Sample:
        """
        Returns the [Sample][cogip.models.models.Sample] model.
        Used to save the samples list.

        Returns:
            The sample model
        """
        return models.Sample(
            id=self._id,
            pos_x=self._pos_x,
            pos_y=self._pos_y,
            pos_z=self._pos_z,
            angle_x=self._angle_x,
            angle_y=self._angle_y,
            angle_z=self._angle_z,
            color=self._color,
            hidden=self._hidden,
            known=self._known
        )

    def update_from_model(self, model: models.Sample) -> None:
        """
        Update sample properties from a sample model
        """
        self.set_pos(model.pos_x, model.pos_y, model.pos_z)
        self.set_angle(model.angle_x, model.angle_y, model.angle_z)
        self._hidden = model.hidden
        self._known = model.known
        self.set_color(model.color)

    @qtSlot(QtGui.QVector3D)
    def new_move_delta(self, delta: QtGui.QVector3D):
        """
        Qt Slot

        Update the sample position.

        Arguments:
            delta: The difference between current and new position
        """
        if self._moving and delta:
            new_translation = self._transform.translation() + delta
            self._transform.setTranslation(new_translation)
            self._properties.spin_x.setValue(new_translation.x())
            self._properties.spin_y.setValue(new_translation.y())


def create_samples(parent: Qt3DCore.QEntity, parent_widget: QtWidgets.QWidget) -> Dict[SampleID, SampleEntity]:
    """
    Add default samples on the table

    Arguments:
            parent: The parent entity
            parent_widget: The parent widget
    """
    samples = {}

    for sample_id in default_samples.keys():
        samples[sample_id] = SampleEntity(sample_id, parent, parent_widget)

    return samples


class SampleProperties(QtWidgets.QDialog):
    """
    The property window.

    Each sample has its own property window.

    Attributes:
        saved_geometry: The position of the last displayed property window
        active_geometry: The current property window displayed.
    """
    saved_geometry: QtCore.QRect = None
    active_properties: "SampleProperties" = None

    def __init__(self, parent: QtWidgets.QWidget, sample_entity: SampleEntity):
        """
        Class constructor.

        Arguments:
            parent: The parent widget
            sample_entity: The related sample entity
        """
        super(SampleProperties, self).__init__(parent)

        self.sample_entity = sample_entity
        self.setWindowTitle("Sample Properties")
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
        self.spin_x.setValue(int(self.sample_entity._pos_x))
        self.spin_x.valueChanged.connect(self.sample_entity.set_pos_x)
        layout.addWidget(label_x, row, 0)
        layout.addWidget(self.spin_x, row, 1)
        row += 1

        label_y = QtWidgets.QLabel("Y")
        self.spin_y = QtWidgets.QSpinBox()
        self.spin_y.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_y.setMinimum(0)
        self.spin_y.setMaximum(2000)
        self.spin_y.setValue(int(self.sample_entity._pos_y))
        self.spin_y.valueChanged.connect(self.sample_entity.set_pos_y)
        layout.addWidget(label_y, row, 0)
        layout.addWidget(self.spin_y, row, 1)
        row += 1

        label_z = QtWidgets.QLabel("Z")
        self.spin_z = QtWidgets.QSpinBox()
        self.spin_z.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        self.spin_z.setMinimum(0)
        self.spin_z.setMaximum(100)
        self.spin_z.setValue(int(self.sample_entity._pos_z))
        self.spin_z.valueChanged.connect(self.sample_entity.set_pos_z)
        layout.addWidget(label_z, row, 0)
        layout.addWidget(self.spin_z, row, 1)
        row += 1

        label_angle_x = QtWidgets.QLabel("X-Angle")
        self.spin_angle_x = QtWidgets.QSpinBox()
        self.spin_angle_x.setSuffix("°")
        self.spin_angle_x.setMinimum(-180)
        self.spin_angle_x.setMaximum(180)
        self.spin_angle_x.setValue(int(self.sample_entity._angle_x))
        self.spin_angle_x.valueChanged.connect(self.sample_entity.set_angle_x)
        layout.addWidget(label_angle_x, row, 0)
        layout.addWidget(self.spin_angle_x, row, 1)
        row += 1

        label_angle_y = QtWidgets.QLabel("Y-Angle")
        self.spin_angle_y = QtWidgets.QSpinBox()
        self.spin_angle_y.setSuffix("°")
        self.spin_angle_y.setMinimum(-180)
        self.spin_angle_y.setMaximum(180)
        self.spin_angle_y.setValue(int(self.sample_entity._angle_y))
        self.spin_angle_y.valueChanged.connect(self.sample_entity.set_angle_y)
        layout.addWidget(label_angle_y, row, 0)
        layout.addWidget(self.spin_angle_y, row, 1)
        row += 1

        label_angle_z = QtWidgets.QLabel("Z-Angle")
        self.spin_angle_z = QtWidgets.QSpinBox()
        self.spin_angle_z.setSuffix("°")
        self.spin_angle_z.setMinimum(-180)
        self.spin_angle_z.setMaximum(180)
        self.spin_angle_z.setValue(int(self.sample_entity._angle_z))
        self.spin_angle_z.valueChanged.connect(self.sample_entity.set_angle_z)
        layout.addWidget(label_angle_z, row, 0)
        layout.addWidget(self.spin_angle_z, row, 1)
        row += 1

        label_color = QtWidgets.QLabel("Color")
        self.combo_color = QtWidgets.QComboBox()
        for color in SampleColor:
            self.combo_color.addItem(color.name, color.value)
        self.combo_color.setCurrentText(self.sample_entity.color.name)
        self.combo_color.currentTextChanged.connect(self.sample_entity.set_color_text)
        layout.addWidget(label_color, row, 0)
        layout.addWidget(self.combo_color, row, 1)
        row += 1

        label_hidden = QtWidgets.QLabel("Hidden")
        self.checkbox_hidden = QtWidgets.QCheckBox()
        self.checkbox_hidden.setChecked(self.sample_entity.hidden)
        self.checkbox_hidden.stateChanged.connect(self.sample_entity.set_hidden)
        layout.addWidget(label_hidden, row, 0)
        layout.addWidget(self.checkbox_hidden, row, 1)
        row += 1

        label_known = QtWidgets.QLabel("Known")
        self.checkbox_known = QtWidgets.QCheckBox()
        self.checkbox_known.setChecked(self.sample_entity.known)
        self.checkbox_known.stateChanged.connect(self.sample_entity.set_known)
        layout.addWidget(label_known, row, 0)
        layout.addWidget(self.checkbox_known, row, 1)
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
    def set_active_properties(cls, properties: "SampleProperties"):
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
        if SampleProperties.saved_geometry:
            self.setGeometry(SampleProperties.saved_geometry)

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Close the property windows.

        Arguments:
            event: The close event (unused)
        """
        SampleProperties.set_saved_geometry(self.geometry())
        SampleProperties.set_active_properties(None)
        event.accept()

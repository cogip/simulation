from PySide2 import QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DExtras import Qt3DExtras


class ImpactEntity(Qt3DCore.QEntity):

    def __init__(self, radius: float = 50, color: QtCore.Qt.GlobalColor = QtCore.Qt.red):
        super(ImpactEntity, self).__init__()

        self.mesh = Qt3DExtras.QSphereMesh()
        self.mesh.setRadius(radius)
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QPhongMaterial()
        self.material.setDiffuse(QtGui.QColor(color))
        self.addComponent(self.material)

        self.transform = Qt3DCore.QTransform()
        self.addComponent(self.transform)
        self.setEnabled(False)

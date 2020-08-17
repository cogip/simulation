from PySide2 import QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DExtras import Qt3DExtras


class ImpactEntity(Qt3DCore.QEntity):

    def __init__(self):
        super(ImpactEntity, self).__init__()

        self.mesh = Qt3DExtras.QSphereMesh()
        self.mesh.setRadius(50)
        self.addComponent(self.mesh)

        self.material = Qt3DExtras.QPhongMaterial()
        self.material.setDiffuse(QtGui.QColor(QtCore.Qt.red))
        self.addComponent(self.material)

        self.transform = Qt3DCore.QTransform()
        self.addComponent(self.transform)
        self.setEnabled(False)

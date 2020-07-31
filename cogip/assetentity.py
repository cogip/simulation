from pathlib import Path
from typing import Union

from PySide2 import QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.QtCore import Slot as qtSlot

from cogip import logger
from cogip.models import PoseCurrent


# tree.txt can be displayed with:
# dot -Tpdf <file>.tree.dot | okular -

def traverse_tree(fd, entity, nextNodeNumber):
    myNodeNumber = nextNodeNumber
    nextNodeNumber += 1

    # Insert current node in the tree
    fd.write("n%03d [label=\"%s\n%s\"] ;\n" % (
          myNodeNumber,
          entity.metaObject().className(),
          entity.objectName()))

    # Enumerate components
    for comp in entity.components():
        fd.write("n%03d [shape=box,label=\"%s\n%s\"] ;\n" % (
              nextNodeNumber,
              comp.metaObject().className(),
              comp.objectName()))
        fd.write("n%03d -- n%03d [style=dotted];\n" % (
              myNodeNumber, nextNodeNumber))
        nextNodeNumber += 1

    # Build tree for children
    for childNode in entity.children():
        if isinstance(childNode, Qt3DCore.QEntity):
            childNodeNumber, nextNodeNumber = traverse_tree(fd, childNode, nextNodeNumber)
            fd.write("n%03d -- n%03d ;\n" % (myNodeNumber, childNodeNumber))

    return myNodeNumber, nextNodeNumber


class AssetEntity(Qt3DCore.QEntity):
    def __init__(self, asset_path: Union[Path, str], asset_name: str = None):
        super(AssetEntity, self).__init__()

        self.asset_ready = False

        if isinstance(asset_path, Path):
            self.asset_path = asset_path
        elif isinstance(asset_path, str):
            self.asset_path = Path(asset_path)
        else:
            raise TypeError("'asset_path' argument must be of type 'str' or 'pathlib.Path'")

        if not self.asset_path.exists():
            raise FileNotFoundError(f"File not found '{self.asset_path}'")
        if not self.asset_path.is_file():
            raise IsADirectoryError(f"'{self.asset_path}' is not a file")

        self.asset_name = asset_name
        self.transform_component = None

        loader = Qt3DRender.QSceneLoader(self)
        loader.statusChanged.connect(self.on_loader_status_changed)
        loader.setObjectName(self.asset_path.name)
        self.addComponent(loader)
        loader.setSource(QtCore.QUrl(f"file:{self.asset_path}"))

    @qtSlot(Qt3DRender.QSceneLoader.Status)
    def on_loader_status_changed(self, status: Qt3DRender.QSceneLoader.Status):
        if status != Qt3DRender.QSceneLoader.Ready:
            return

        # In PyQt5 5.15.0
        # Warning: QEntity.childNodes() can be called only once
        #   The second time, it returns an empty list
        #   => Use QEntity.children() instead
        # Warning: QEntity.components() can be called only once
        #   The second time, it returns an empty list
        #   => No solution right now other than using PySide2

        # Write tree file (graphviz format)
        tree_filename = self.asset_path.with_suffix(".tree.dot")
        with tree_filename.open(mode='w') as fd:
            fd.write('graph ""\n')
            fd.write('{\n')
            fd.write('label="Entity tree"\n')
            root_node_number = 0
            traverse_tree(fd, self, root_node_number)
            fd.write("}\n")

        if self.asset_name:
            # Find the transform component of the entity
            asset_entity = self.findChild(Qt3DCore.QEntity, self.asset_name)
            if not asset_entity:
                logger.warning(f"Entity '{self.asset_name} not found in {self.asset_path}")
            else:
                for comp in asset_entity.components():
                    if isinstance(comp, Qt3DCore.QTransform):
                        self.transform_component = comp
                        break

        self.asset_ready = True

    @qtSlot(PoseCurrent)
    def set_position(self, new_position: PoseCurrent) -> None:
        if not self.transform_component:
            return

        self.transform_component.setTranslation(
            QtGui.QVector3D(new_position.x, new_position.y, 0))
        self.transform_component.setRotationZ(new_position.O)

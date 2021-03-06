"""
This module defines the base class [AssetEntity][cogip.assetentity.AssetEntity]
used directly or inherited for specific assets.

Asset entities are graphic element displayed on the 3D view and loaded from asset files.
It is typically used for table and robot assets.

Supported asset files are in [Collada](https://en.wikipedia.org/wiki/COLLADA) format (`.dae`).
Other formats could be also supported, but not tested
(see [Open Asset Import Library](https://github.com/assimp/assimp)).
"""

from pathlib import Path
from typing import TextIO, Tuple, Union

from PySide2 import QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.QtCore import Signal as qtSignal
from PySide2.QtCore import Slot as qtSlot

from cogip import logger
from cogip.models import RobotState


class AssetEntity(Qt3DCore.QEntity):
    """Base class for asset entities

    This class inherits from [`Qt3DCore.QEntity`](https://doc.qt.io/qtforpython/PySide2/Qt3DCore/QEntity.html)

    Attributes:
        ready: Qt signal emitted when the asset entity is ready to be used
        asset_ready: `True` if the asset is ready
        asset_entity: first useful `QEntity` in the asset tree
        transform_component: `QTransform` holding the asset's translation and orientation
    """

    ready: qtSignal = qtSignal()

    def __init__(self, asset_path: Union[Path, str], asset_name: str = None):
        """
        The constructor checks the asset's file and starts loading the entity.

        The entity load is asynchronous, a signal is emitted when it is done
        (see [`on_loader_status_changed`][cogip.assetentity.AssetEntity.on_loader_status_changed])

        Arguments:
            asset_path: path of the asset file
            asset_name: asset name
        """

        super(AssetEntity, self).__init__()

        self.asset_ready: bool = False
        self.asset_path: Path = None
        self.asset_name: str = asset_name
        self.asset_entity: Qt3DCore.QEntity = None
        self.transform_component: Qt3DCore.QTransform = None

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

        self.loader = Qt3DRender.QSceneLoader(self)
        self.loader.statusChanged.connect(self.on_loader_status_changed)
        self.loader.setObjectName(self.asset_path.name)
        self.addComponent(self.loader)
        self.loader.setSource(QtCore.QUrl(f"file:{self.asset_path}"))

    @qtSlot(Qt3DRender.QSceneLoader.Status)
    def on_loader_status_changed(self, status: Qt3DRender.QSceneLoader.Status):
        """
        When the loader has finished, clean the entity tree,
        record the main `QEntity` and its `QTransform` component.

        Then it generated the dot tree
        (see [`generate_tree`][cogip.assetentity.AssetEntity.generate_tree]),
        run the [`post_init`][cogip.assetentity.AssetEntity.post_init] pass,
        and emit the `ready` signal.

        Arguments:
            status: current loader status
        """

        if status != Qt3DRender.QSceneLoader.Ready:
            return

        if self.asset_name:
            # Find the asset entity
            self.asset_entity = self.findChild(Qt3DCore.QEntity, self.asset_name)
            if not self.asset_entity:
                logger.warning(f"Entity '{self.asset_name}' not found in {self.asset_path}")
            else:
                # Set asset entity as the first child
                self.asset_entity.setParent(self)
                # Find the transform component of the asset entity
                for comp in self.asset_entity.components():
                    if isinstance(comp, Qt3DCore.QTransform):
                        self.transform_component = comp
                        break

        # Remove unused entities and component
        self.scene_entity = self.findChild(Qt3DCore.QEntity, "Scene")
        self.scene_entity.setParent(None)
        self.removeComponent(self.loader)

        self.generate_tree()

        self.post_init()

        self.asset_ready = True

        self.ready.emit()

    @qtSlot(RobotState)
    def set_position(self, new_state: RobotState) -> None:
        """
        Qt slot called to set the entity's new position.

        Arguments:
            new_state: new robot state
        """

        if not self.transform_component:
            return
        self.transform_component.setTranslation(
            QtGui.QVector3D(new_state.pose_current.x, new_state.pose_current.y, 0))
        self.transform_component.setRotationZ(new_state.pose_current.O + 90)

    def generate_tree(self):
        """
        Generate a tree of all entities and components starting from the main entity.

        The generated file is stored next to the asset file and it has the same name
        but with `.tree.dot` extension.

        It is a text file written in [Graphviz](https://graphviz.org/) format.

        To read this file:
        ```bash
            sudo apt install graphviz okular
            dot -Tpdf assets/robot2019.tree.dot | okular -
        ```
        """

        tree_filename = self.asset_path.with_suffix(".tree.dot")
        with tree_filename.open(mode='w') as fd:
            fd.write('graph ""\n')
            fd.write('{\n')
            fd.write('label="Entity tree"\n')
            root_node_number = 0
            traverse_tree(self, root_node_number, fd)
            fd.write("}\n")

    def post_init(self):
        """
        Post initialization method that can be overloaded.
        It it executed after entity and transform components are ready.
        """
        pass


def traverse_tree(node: Qt3DCore.QEntity, next_node_nb: int, fd: TextIO) -> Tuple[int, int]:
    """
    Recursive function traversing all child entities and write its node
    and all its components to the .dot file.

    Arguments:
        node: entity to traverse
        next_node_nb: next node number
        fd: opened file descriptor used to write the tree

    Return:
        tuple of current and next node numbers
    """

    current_node_nb = next_node_nb
    next_node_nb += 1

    # Insert current node in the tree
    fd.write("n%03d [label=\"%s\n%s\"] ;\n" % (
        current_node_nb,
        node.metaObject().className(),
        node.objectName()))

    # Enumerate components
    for comp in node.components():
        fd.write("n%03d [shape=box,label=\"%s\n%s\"] ;\n" % (
            next_node_nb,
            comp.metaObject().className(),
            comp.objectName()))
        fd.write("n%03d -- n%03d [style=dotted];\n" % (
            current_node_nb, next_node_nb))
        next_node_nb += 1

    # Build tree for children
    for child_node in node.children():
        if isinstance(child_node, Qt3DCore.QEntity):
            child_node_nb, next_node_nb = traverse_tree(child_node, next_node_nb, fd)
            fd.write("n%03d -- n%03d ;\n" % (current_node_nb, child_node_nb))

    return current_node_nb, next_node_nb

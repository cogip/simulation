from pathlib import Path
import math
from queue import Queue

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal as qtSignal

import OCC.Core.TDF
import OCC.Core.TopLoc
import OCC.Extend.DataExchange

from cogip import logger
from cogip.models import PoseCurrent


def get_sub_shapes(lab, loc, shape_tool, color_tool, shapes):
    # users = OCC.Core.TDF.TDF_LabelSequence()
    # users_cnt = shape_tool.GetUsers(lab, users)

    if shape_tool.IsAssembly(lab):
        l_c = OCC.Core.TDF.TDF_LabelSequence()
        shape_tool.GetComponents(lab, l_c)
        for i in range(l_c.Length()):
            label = l_c.Value(i+1)
            if shape_tool.IsReference(label):
                label_reference = OCC.Core.TDF.TDF_Label()
                shape_tool.GetReferredShape(label, label_reference)
                loc = shape_tool.GetLocation(label)
                # tran = loc.Transformation()
                # q = tran.GetRotation()

                get_sub_shapes(label_reference, loc, shape_tool, color_tool, shapes)

    elif shape_tool.IsShape(lab):
        shape = shape_tool.GetShape(lab)
        if loc:
            shape.Move(loc)

        c = OCC.Core.Quantity.Quantity_Color()
        if (color_tool.GetColor(lab, 0, c)
                or color_tool.GetColor(lab, 1, c)
                or color_tool.GetColor(lab, 2, c)):
            for i in (0, 1, 2):
                color_tool.SetInstanceColor(shape, i, c)

        # n = c.Name(c.Red(), c.Green(), c.Blue())
        shape.color = c
        shapes.append(shape)


def read_step_file_with_names_colors_as_shapes(filename):
    if not Path(filename).exists:
        raise FileNotFoundError(f"{filename} not found.")

    output_shapes = []

    # create an handle to a document
    doc = OCC.Core.TDocStd.TDocStd_Document(OCC.Core.TCollection.TCollection_ExtendedString("pythonocc-doc"))

    # Get root assembly
    shape_tool = OCC.Core.XCAFDoc.XCAFDoc_DocumentTool_ShapeTool(doc.Main())
    color_tool = OCC.Core.XCAFDoc.XCAFDoc_DocumentTool_ColorTool(doc.Main())
    # layer_tool = OCC.Core.XCAFDoc.XCAFDoc_DocumentTool_LayerTool(doc.Main())
    # mat_tool = OCC.Core.XCAFDoc.XCAFDoc_DocumentTool_MaterialTool(doc.Main())

    step_reader = OCC.Core.STEPCAFControl.STEPCAFControl_Reader()
    step_reader.SetColorMode(True)
    step_reader.SetLayerMode(True)
    step_reader.SetNameMode(True)
    step_reader.SetMatMode(True)
    # step_reader.SetGDTMode(True)

    status = step_reader.ReadFile(str(filename))
    if status == OCC.Core.IFSelect.IFSelect_RetDone:
        step_reader.Transfer(doc)

    labels = OCC.Core.TDF.TDF_LabelSequence()
    # color_labels = OCC.Core.TDF.TDF_LabelSequence()

    shape_tool.GetFreeShapes(labels)

    root = labels.Value(1)
    get_sub_shapes(root, None, shape_tool, color_tool, output_shapes)

    return output_shapes


class Robot(QtCore.QObject):
    """Robot class

    Load the robot model from a STEP file, display and move it.

    Args:
            robot_filename (Path): filename of the robot model
            position_queue (Queue):
                Queue containing robot position,
                filled by :class:`~cogip.serialcontroller.SerialController`
    """

    #: :obj:`qtSignal(float, float, float)`:
    #:      Qt signal emitted to update Robot postion.
    #:      Parameter is a :class:`~cogip.models.PoseCurrent`.
    #:
    #:      Connected to :class:`~cogip.mainwindow.MainWindow`.
    signal_position_updated = qtSignal(PoseCurrent)

    def __init__(self, robot_filename: Path, position_queue: Queue):
        QtCore.QObject.__init__(self)
        self.position_queue = position_queue

        if QtWidgets.QApplication.instance() is not None:
            logger.error("Robot shapes must be initialized before QApplication is started")
            return None

        self.ais_shapes = []
        shapes = read_step_file_with_names_colors_as_shapes(robot_filename)
        self.shape = shapes[0]
        if not hasattr(self.shape, 'color'):
            self.shape.color = OCC.Core.Quantity.Quantity_Color()

    def set_display(self, display):
        self.display = display
        self.ais_shape = self.display.DisplayColoredShape(self.shape, color=self.shape.color, update=True)

    def update_position(self):
        while True:
            pose: PoseCurrent = self.position_queue.get()

            teta = math.radians(pose.O + 90)

            vector = OCC.Core.gp.gp_Vec(
                pose.x,
                pose.y,
                0
            )
            ax = OCC.Core.gp.gp_Ax1(
                OCC.Core.gp.gp_Pnt(0., 0., 0.),
                OCC.Core.gp.gp_Dir(0., 0., 1.)
            )
            translate = OCC.Core.gp.gp_Trsf()
            rotate = OCC.Core.gp.gp_Trsf()
            translate.SetTranslation(vector)
            rotate.SetRotation(ax, teta)

            toploc = OCC.Core.TopLoc.TopLoc_Location(translate * rotate)

            self.display.Context.SetLocation(self.ais_shape, toploc)

            self.display.Context.UpdateCurrentViewer()

            self.signal_position_updated.emit(pose)
            self.position_queue.task_done()

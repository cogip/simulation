from PyQt5 import QtWidgets

import OCC

from cogip import logger


class Table:
    """Table class

    Load the table model from a IGES file and display it.

    Args:
            table_filename (Path): filename of the table model
    """

    def __init__(self, table_filename):
        if QtWidgets.QApplication.instance() is not None:
            logger.error("Table class must be created before QApplication is started")
            return None
        table_shapes = OCC.Extend.DataExchange.read_iges_file(
            filename=str(table_filename),
            return_as_shapes=True,
            verbosity=False,
            visible_only=False)
        self.table_shape = table_shapes[0]
        if not hasattr(self.table_shape, 'color'):
            self.table_shape.color = OCC.Core.Quantity.Quantity_Color()

    def set_display(self, display):
        self.display = display
        self.display.DisplayColoredShape(self.table_shape, color=self.table_shape.color, update=True)

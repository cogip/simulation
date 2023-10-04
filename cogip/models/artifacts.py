# flake8: noqa
from enum import auto, IntEnum

from pydantic import BaseModel

from .models import Vertex


class CakeLayerID(IntEnum):
    """
    Enum to identify each cake layer
    """
    GREEN_FRONT_ICING_BOTTOM = auto()
    GREEN_FRONT_ICING_MIDDLE = auto()
    GREEN_FRONT_ICING_TOP = auto()
    GREEN_FRONT_CREAM_BOTTOM = auto()
    GREEN_FRONT_CREAM_MIDDLE = auto()
    GREEN_FRONT_CREAM_TOP = auto()
    GREEN_FRONT_SPONGE_BOTTOM = auto()
    GREEN_FRONT_SPONGE_MIDDLE = auto()
    GREEN_FRONT_SPONGE_TOP = auto()

    GREEN_BACK_SPONGE_BOTTOM = auto()
    GREEN_BACK_SPONGE_MIDDLE = auto()
    GREEN_BACK_SPONGE_TOP = auto()
    GREEN_BACK_CREAM_BOTTOM = auto()
    GREEN_BACK_CREAM_MIDDLE = auto()
    GREEN_BACK_CREAM_TOP = auto()
    GREEN_BACK_ICING_BOTTOM = auto()
    GREEN_BACK_ICING_MIDDLE = auto()
    GREEN_BACK_ICING_TOP = auto()

    BLUE_FRONT_ICING_BOTTOM = auto()
    BLUE_FRONT_ICING_MIDDLE = auto()
    BLUE_FRONT_ICING_TOP = auto()
    BLUE_FRONT_CREAM_BOTTOM = auto()
    BLUE_FRONT_CREAM_MIDDLE = auto()
    BLUE_FRONT_CREAM_TOP = auto()
    BLUE_FRONT_SPONGE_BOTTOM = auto()
    BLUE_FRONT_SPONGE_MIDDLE = auto()
    BLUE_FRONT_SPONGE_TOP = auto()

    BLUE_BACK_SPONGE_BOTTOM = auto()
    BLUE_BACK_SPONGE_MIDDLE = auto()
    BLUE_BACK_SPONGE_TOP = auto()
    BLUE_BACK_CREAM_BOTTOM = auto()
    BLUE_BACK_CREAM_MIDDLE = auto()
    BLUE_BACK_CREAM_TOP = auto()
    BLUE_BACK_ICING_BOTTOM = auto()
    BLUE_BACK_ICING_MIDDLE = auto()
    BLUE_BACK_ICING_TOP = auto()


class CakeSlotID(IntEnum):
    """
    Enum to identify each cake pickup slot
    """
    GREEN_FRONT_SPONGE = auto()
    GREEN_FRONT_CREAM = auto()
    GREEN_FRONT_ICING = auto()

    GREEN_BACK_SPONGE = auto()
    GREEN_BACK_CREAM = auto()
    GREEN_BACK_ICING = auto()

    BLUE_FRONT_SPONGE = auto()
    BLUE_FRONT_CREAM = auto()
    BLUE_FRONT_ICING = auto()

    BLUE_BACK_SPONGE = auto()
    BLUE_BACK_CREAM = auto()
    BLUE_BACK_ICING = auto()


class CakeLayerKind(IntEnum):
    """
    Enum for cake layers

    Attributes:
        ICING:
        CREAM:
        SPONGE:
    """
    ICING = auto()
    CREAM = auto()
    SPONGE = auto()


class CakeLayerPos(IntEnum):
    """
    Enum for cake layer positions

    Attributes:
        TOP:
        MIDDLE:
        BOTTOM:
    """
    TOP = auto()
    MIDDLE = auto()
    BOTTOM = auto()


class CakeLayer(BaseModel):
    """
    Contains the properties of a cake layer on the table.

    Attributes:
        id: cake layer id
        x: X coordinate
        y: Y coordinate
        pos: layer position
        kind: layer kind
    """
    id: CakeLayerID
    x: float
    y: float
    pos: CakeLayerPos
    kind: CakeLayerKind

    @property
    def vertex(self) -> Vertex:
        return Vertex(x=self.x, y=self.y)


class CherryID(IntEnum):
    """
    Enum to identify each cherry
    """
    FRONT_1 = auto()
    FRONT_2 = auto()
    FRONT_3 = auto()
    FRONT_4 = auto()
    FRONT_5 = auto()
    FRONT_6 = auto()
    FRONT_7 = auto()
    FRONT_8 = auto()
    FRONT_9 = auto()
    FRONT_10 = auto()

    BACK_1 = auto()
    BACK_2 = auto()
    BACK_3 = auto()
    BACK_4 = auto()
    BACK_5 = auto()
    BACK_6 = auto()
    BACK_7 = auto()
    BACK_8 = auto()
    BACK_9 = auto()
    BACK_10 = auto()

    GREEN_1 = auto()
    GREEN_2 = auto()
    GREEN_3 = auto()
    GREEN_4 = auto()
    GREEN_5 = auto()
    GREEN_6 = auto()
    GREEN_7 = auto()
    GREEN_8 = auto()
    GREEN_9 = auto()
    GREEN_10 = auto()

    BLUE_1 = auto()
    BLUE_2 = auto()
    BLUE_3 = auto()
    BLUE_4 = auto()
    BLUE_5 = auto()
    BLUE_6 = auto()
    BLUE_7 = auto()
    BLUE_8 = auto()
    BLUE_9 = auto()
    BLUE_10 = auto()

    ROBOT_1 = auto()
    ROBOT_2 = auto()
    ROBOT_3 = auto()
    ROBOT_4 = auto()
    ROBOT_5 = auto()
    ROBOT_6 = auto()
    ROBOT_7 = auto()
    ROBOT_8 = auto()
    ROBOT_9 = auto()
    ROBOT_10 = auto()

    OPPONENT_1 = auto()
    OPPONENT_2 = auto()
    OPPONENT_3 = auto()
    OPPONENT_4 = auto()
    OPPONENT_5 = auto()
    OPPONENT_6 = auto()
    OPPONENT_7 = auto()
    OPPONENT_8 = auto()
    OPPONENT_9 = auto()
    OPPONENT_10 = auto()


class CherryLocation(IntEnum):
    """
    Enum for cherry locations

    Attributes:
        TOP:
        MIDDLE:
        BOTTOM:
        RACK:
        ROBOT:
        OPPONENT:
        BASKET:
    """
    TOP = auto()
    MIDDLE = auto()
    BOTTOM = auto()
    RACK = auto()
    ROBOT = auto()
    OPPONENT = auto()
    BASKET = auto()


# Default position and properties of all cake layers
default_cake_layers: dict[CakeLayerID, tuple[float, float, CakeLayerKind, CakeLayerPos]] = {
    # Cake Layer ID:                       (x,                  y,               kind,                position)

    # Green Back quarter
    CakeLayerID.GREEN_BACK_ICING_BOTTOM:  (450+125,            1000-225,        CakeLayerKind.ICING, CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_BACK_ICING_MIDDLE:  (450+125,            1000-225,        CakeLayerKind.ICING, CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_BACK_ICING_TOP:     (450+125,            1000-225,        CakeLayerKind.ICING, CakeLayerPos.TOP),

    CakeLayerID.GREEN_BACK_CREAM_BOTTOM:  (450+125+200,        1000-225,        CakeLayerKind.CREAM, CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_BACK_CREAM_MIDDLE:  (450+125+200,        1000-225,        CakeLayerKind.CREAM, CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_BACK_CREAM_TOP:     (450+125+200,        1000-225,        CakeLayerKind.CREAM, CakeLayerPos.TOP),

    CakeLayerID.GREEN_BACK_SPONGE_BOTTOM: (1125,               1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_BACK_SPONGE_MIDDLE: (1125,               1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_BACK_SPONGE_TOP:    (1125,               1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.TOP),

    # Green Front quarter
    CakeLayerID.GREEN_FRONT_SPONGE_BOTTOM:  (3000-1125,          1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_FRONT_SPONGE_MIDDLE:  (3000-1125,          1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_FRONT_SPONGE_TOP:     (3000-1125,          1000-350-375,    CakeLayerKind.SPONGE, CakeLayerPos.TOP),

    CakeLayerID.GREEN_FRONT_CREAM_BOTTOM:   (3000-(450+125+200), 1000-225,        CakeLayerKind.CREAM,  CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_FRONT_CREAM_MIDDLE:   (3000-(450+125+200), 1000-225,        CakeLayerKind.CREAM,  CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_FRONT_CREAM_TOP:      (3000-(450+125+200), 1000-225,        CakeLayerKind.CREAM,  CakeLayerPos.TOP),

    CakeLayerID.GREEN_FRONT_ICING_BOTTOM:   (3000-(450+125),     1000-225,        CakeLayerKind.ICING,  CakeLayerPos.BOTTOM),
    CakeLayerID.GREEN_FRONT_ICING_MIDDLE:   (3000-(450+125),     1000-225,        CakeLayerKind.ICING,  CakeLayerPos.MIDDLE),
    CakeLayerID.GREEN_FRONT_ICING_TOP:      (3000-(450+125),     1000-225,        CakeLayerKind.ICING,  CakeLayerPos.TOP),

    # Blue Back quarter
    CakeLayerID.BLUE_BACK_ICING_BOTTOM:   (450+125,            -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_BACK_ICING_MIDDLE:   (450+125,            -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_BACK_ICING_TOP:      (450+125,            -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.TOP),

    CakeLayerID.BLUE_BACK_CREAM_BOTTOM:   (450+125+200,        -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_BACK_CREAM_MIDDLE:   (450+125+200,        -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_BACK_CREAM_TOP:      (450+125+200,        -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.TOP),

    CakeLayerID.BLUE_BACK_SPONGE_BOTTOM:  (1125,               -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_BACK_SPONGE_MIDDLE:  (1125,               -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_BACK_SPONGE_TOP:     (1125,               -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.TOP),

    # Blue Front quarter
    CakeLayerID.BLUE_FRONT_SPONGE_BOTTOM:   (3000-1125,          -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_FRONT_SPONGE_MIDDLE:   (3000-1125,          -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_FRONT_SPONGE_TOP:      (3000-1125,          -(1000-350-375), CakeLayerKind.SPONGE, CakeLayerPos.TOP),

    CakeLayerID.BLUE_FRONT_CREAM_BOTTOM:    (3000-(450+125+200), -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_FRONT_CREAM_MIDDLE:    (3000-(450+125+200), -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_FRONT_CREAM_TOP:       (3000-(450+125+200), -(1000-225),     CakeLayerKind.CREAM,  CakeLayerPos.TOP),

    CakeLayerID.BLUE_FRONT_ICING_BOTTOM:    (3000-(450+125),     -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.BOTTOM),
    CakeLayerID.BLUE_FRONT_ICING_MIDDLE:    (3000-(450+125),     -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.MIDDLE),
    CakeLayerID.BLUE_FRONT_ICING_TOP:       (3000-(450+125),     -(1000-225),     CakeLayerKind.ICING,  CakeLayerPos.TOP)
}

default_cake_slots: dict[CakeSlotID, tuple[float, float, CakeLayerKind]] = {
    # Cake Slot ID:                       (x,                  y,               kind)

    # Green Back quarter
    CakeSlotID.GREEN_BACK_ICING:  (450+125,            1000-225,        CakeLayerKind.ICING),
    CakeSlotID.GREEN_BACK_CREAM:  (450+125+200,        1000-225,        CakeLayerKind.CREAM),
    CakeSlotID.GREEN_BACK_SPONGE: (1125,               1000-350-375,    CakeLayerKind.SPONGE),

    # Green Front quarter
    CakeSlotID.GREEN_FRONT_SPONGE:  (3000-1125,          1000-350-375,    CakeLayerKind.SPONGE),
    CakeSlotID.GREEN_FRONT_CREAM:   (3000-(450+125+200), 1000-225,        CakeLayerKind.CREAM),
    CakeSlotID.GREEN_FRONT_ICING:   (3000-(450+125),     1000-225,        CakeLayerKind.ICING),

    # Blue Back quarter
    CakeSlotID.BLUE_BACK_ICING:   (450+125,            -(1000-225),     CakeLayerKind.ICING),
    CakeSlotID.BLUE_BACK_CREAM:   (450+125+200,        -(1000-225),     CakeLayerKind.CREAM),
    CakeSlotID.BLUE_BACK_SPONGE:  (1125,               -(1000-350-375), CakeLayerKind.SPONGE),

    # Blue Front quarter
    CakeSlotID.BLUE_FRONT_SPONGE:   (3000-1125,          -(1000-350-375), CakeLayerKind.SPONGE),
    CakeSlotID.BLUE_FRONT_CREAM:    (3000-(450+125+200), -(1000-225),     CakeLayerKind.CREAM),
    CakeSlotID.BLUE_FRONT_ICING:    (3000-(450+125),     -(1000-225),     CakeLayerKind.ICING),
}

# Default position and properties of all cherries
default_cherries: dict[CherryID, tuple[float, float, CherryLocation]] = {
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

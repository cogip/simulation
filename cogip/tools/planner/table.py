from enum import IntEnum

from pydantic import BaseModel

from cogip.models.models import Vertex


class TableEnum(IntEnum):
    """
    Enum for available tables.
    """
    Training = 0
    Game = 1


class Table(BaseModel):
    x_min: int
    x_max: int
    y_min: int
    y_max: int

    def contains(self, point: Vertex, margin: int = 0) -> bool:
        return point.x >= self.x_min + margin \
            and point.x <= self.x_max - margin \
            and point.y >= self.y_min + margin \
            and point.y <= self.y_max - margin


table_training = Table(x_min=1500, x_max=3000, y_min=-1000, y_max=0)
table_game = Table(x_min=0, x_max=3000, y_min=-1000, y_max=1000)

tables: dict[TableEnum, Table] = {
    TableEnum.Training: table_training,
    TableEnum.Game: table_game
}

from pydantic import BaseModel, Field


class Properties(BaseModel):
    min_distance: int = Field(
        ..., ge=0, le=1000,
        title="Min Distance",
        description="Minimum distance to detect an obstacle (mm)"
    )
    max_distance: int = Field(
        ..., ge=0, le=3000,
        title="Max Distance",
        description="Maximum distance to detect an obstacle (mm)"
    )
    obstacle_radius: int = Field(
        ..., ge=100, le=1000,
        title="Obstacle Radius",
        description="Radius of a dynamic obstacle (mm)"
    )
    obstacle_bb_margin: float = Field(
        ..., ge=0, le=1, multiple_of=0.01,
        title="Bounding Box Margin",
        description="Obstacle bounding box margin in percent of the radius (%)"
    )
    obstacle_bb_vertices: int = Field(
        ..., ge=3, le=20,
        title="Bounding Box Vertices",
        description="Number of obstacle bounding box vertices"
    )
    beacon_radius: int = Field(
        ..., ge=10, le=150,
        title="Opponent Beacon Radius",
        description="Radius of the opponent beacon support (mm)"
    )
    refresh_interval: float = Field(
        ..., ge=0.1, le=2.0, multiple_of=0.05,
        title="Refresh Interval",
        description="Interval between each update of the obstacle list (seconds)"
    )

    class Config:
        title = "Detector Properties"

from pydantic import BaseModel, Field


class Properties(BaseModel):
    min_distance: int = Field(
        ..., ge=0, le=1000,
        title="Min Distance",
        description="Minimum distance to detect an obstacle (mm)"
    )
    max_distance: int = Field(
        ..., ge=0, le=4000,
        title="Max Distance",
        description="Maximum distance to detect an obstacle (mm)"
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

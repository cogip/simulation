from pydantic import BaseModel, Field


class Properties(BaseModel):
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
    obstacle_sender_interval: float = Field(
        ..., ge=0.1, le=2.0, multiple_of=0.05,
        title="Obstacle Sender Interval",
        description="Interval between each send of obstacles to dashboards (seconds)"
    )
    path_refresh_interval: float = Field(
        ..., ge=0.1, le=2.0, multiple_of=0.05,
        title="Path Refresh Interval",
        description="Interval between each update of robot paths (seconds)"
    )

    class Config:
        title = "Planner Properties"

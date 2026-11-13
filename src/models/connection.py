from pydantic import BaseModel, Field


class Connection(BaseModel):
    """Define a bidirectional connection (edge) between two zones"""
    zones: tuple[str, str] = Field(
        description="Pair of connected zone names (zone_a, zone_b)"
    )
    max_link_capacity: int = Field(
        default=1,
        ge=1,
        description="Maximum drones that can occupy this "
                    "connection simultaneously"
    )
    current_drones_count: int = Field(
        default=0,
        ge=0,
        description=(
            "Current number of drones traversing this connection "
            "in the current turn"
        ),
    )

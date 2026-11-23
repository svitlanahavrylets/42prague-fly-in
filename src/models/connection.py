from pydantic import BaseModel, Field


class Connection(BaseModel):
    """Represent a bidirectional link between two zones."""
    zones: tuple[str, str] = Field(
        description="Pair of connected zone names (zone_a, zone_b)"
    )
    max_link_capacity: int = Field(
        default=1,
        ge=1,
        description="Maximum drones that can occupy this "
                    "connection simultaneously"
    )

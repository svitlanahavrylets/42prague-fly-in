from pydantic import BaseModel, Field
from enum import Enum


class ZoneType(str, Enum):
    """Supported zone types in the simulation."""
    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class Zone(BaseModel):
    """Reprezents a graph node (zone/hub) in the network"""
    name: str = Field(
        min_length=1, 
        description="Name of the zone"
    )
    x: int = Field(
        description="X of zone's coordinate"
    )
    y: int = Field(
        description="Y of zone's coordinate"
    )
    zone_type: ZoneType = Field(
        ZoneType.NORMAL,
        description="Type of the zone, default normal"
    )
    max_drones: int = Field(
        default=1, 
        ge=1,
        description="Maximum drones that can occupy this zone simultaneously"
    )
    current_drones: list[int] = Field(
        default_factory=list,
        description="List of drone IDs currently occupying this zone"
    )
    color: str | None = Field(
        default=None,
        description="Optional visual color of the zone"
    )
    is_start: bool = Field(default=False, description="Is this the start_hub")
    is_end: bool = Field(default=False, description="Is this the end_hub")

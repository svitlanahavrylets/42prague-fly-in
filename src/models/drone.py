from pydantic import BaseModel, Field


class Drone(BaseModel):
    """Represents an individual drone unit in the simulation."""
    id: int = Field(
        ge=1,
        description="A unique name of drone"
    )
    current_zone: str = Field(
        description="Name of the zone where the drone is currently located"
    )
    path: list[tuple[str, int]] = Field(
        default_factory=list,
        description="Planned space-time path as (zone_name, turn) steps",
    )

    @classmethod
    def create_fleet(cls, count: int, start_location: str) -> list["Drone"]:
        """Generate drones initialized at the start location."""
        return [
            cls(id=i + 1, current_zone=start_location)
            for i in range(count)
        ]

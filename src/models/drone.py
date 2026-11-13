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
    target_zone: str | None = Field(
        default=None,
        description="Destination zone name if drone is in transit"
    )
    remaining_turns: int = Field(
        default=0,
        ge=0,
        description=(
            "Turns remaining to reach target_zone (2 for restricted "
            "movement step 1, 0 if arrived)"
        ),
    )
    has_reached_end: bool = Field(
        default=False,
        description="True if the drone has reached end_hub and is delivered"
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

    def get_position_at_turn(self, turn: int) -> str | None:
        """
        Return the zone scheduled for this drone at the given turn.
        Returns None if no move is registered for this turn.
        """
        for zone_name, t in self.path:
            if t == turn:
                return zone_name
        return None

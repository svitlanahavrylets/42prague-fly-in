from pydantic import BaseModel, Field


class Drone(BaseModel):
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
        description="Turns remaining to reach target_zone (2 for restricted movement step 1, 0 if arrived)"
    )
    has_reached_end: bool = Field(
        default=False,
        description="True if the drone has reached end_hub and is delivered"
    )
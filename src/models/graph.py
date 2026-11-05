from pydantic import BaseModel, Field
from .zone import ZoneType, Zone
from .connection import Connection


class Graph(BaseModel):
    """Represents the entire simulation graph network."""

    zones: dict[str, Zone] = Field(
        default_factory=dict,
        description="Map of zone names to Zone objects"
    )
    connections: list[Connection] = Field(
        default_factory=list,
        description="List of all connections (edges) in the graph"
    )
    start_zone_name: str = Field(
        description="Name of the unique start_hub"
    )
    end_zone_name: str = Field(
        description="Name of the unique end_hub"
    )

    def get_neighbors(self, zone_name: str) -> list[tuple[Zone, Connection, int]]:
        """Return a list of tuples for accessible neighbors:
        (target_zone, connection_used, movement_cost)
        Filters out BLOCKED zones."""
        neighbors: list[tuple[Zone, Connection, int]] = []

        for conn in self.connections:
            target_name: str | None = None
            if conn.zones[0] == zone_name:
                target_name = conn.zones[1]
            elif conn.zones[1] == zone_name:
                target_name = conn.zones[0]

            if target_name is not None:
                target_zone = self.zones[target_name]

                if target_zone.zone_type == ZoneType.BLOCKED:
                        continue

                if target_zone.zone_type == ZoneType.RESTRICTED:
                    cost = 2 
                else:
                    cost = 1

                neighbors.append((target_zone, conn, cost))
            
        return neighbors



class TemporalState:
    """Represents a drone's state in space and time during A* search."""
    def __init__ (
        self,
        zone_name: str,
        turn: int,
        g_cost: float,
        h_cost: float,
        parent: TemporalState | None = None,
        visited_zones: set[str] | None = None
    ) -> None:
    self.zone_name =  zone_name
    self.turn = turn
    self.g_cost = g_cost
    self.h_cost = h_cost
    self.parent = parent
    self.visited_zones = visited_zones if visited_zones is not None else {zone_name}

    @property
    def f_cost(self) -> float:
        return self.g_cost + self.h_cost

    def __lt__(self, other: TemporalState) -> bool:
        return self.f_cost < other.f_cost
"""Run the simulation and record drone locations for visualization."""

from dataclasses import dataclass

from ..models import Drone


@dataclass(frozen=True)
class TurnSnapshot:
    """Store drone locations and zone counts for one simulation turn."""

    turn: int
    drone_locations: dict[int, str]
    zone_counts: dict[str, int]


class SimulationController:
    """Build turn snapshots and print the drone movements."""

    def __init__(self, drones: list[Drone]) -> None:
        """Create a controller for the planned drone paths."""
        self.drones: list[Drone] = drones
        self.history: list[TurnSnapshot] = []

    def _get_drone_action(self, drone: Drone, turn: int) -> (
        tuple[str | None, str]
    ):
        """Return the movement text and location for one drone and turn."""
        if turn == 0:
            return None, drone.path[0][0]

        for i in range(1, len(drone.path)):
            prev_zone, prev_turn = drone.path[i - 1]
            curr_zone, curr_turn = drone.path[i]

            if curr_turn == turn:
                if prev_zone != curr_zone:
                    return f"D{drone.id}-{curr_zone}", curr_zone
                return None, curr_zone

            if prev_turn < turn < curr_turn:
                conn_name = f"{prev_zone}-{curr_zone}"
                return f"D{drone.id}-{conn_name}", conn_name

        return None, drone.path[-1][0]

    def _get_max_turn(self) -> int:
        """Return the last turn used by any drone path."""
        max_turn = 0
        for drone in self.drones:
            if not drone.path:
                raise ValueError(f"Path for Drone {drone.id} does not exist")

            max_item = drone.path[-1][1]
            if max_item > max_turn:
                max_turn = max_item
        return max_turn

    def _record_snapshot(
        self, turn: int, drone_locations: dict[int, str]
    ) -> None:
        """Save drone locations and zone occupancy for one turn."""
        zone_counts: dict[str, int] = {}

        for location in drone_locations.values():
            if "-" not in location:
                zone_counts[location] = zone_counts.get(location, 0) + 1

        snapshot = TurnSnapshot(
            turn=turn,
            drone_locations=drone_locations,
            zone_counts=zone_counts,
        )
        self.history.append(snapshot)

    def run(self) -> None:
        """Print each turn and store its state in the history."""
        self.history.clear()
        max_turn = self._get_max_turn()

        initial_locations: dict[int, str] = {}

        for drone in self.drones:
            _, location = self._get_drone_action(drone, 0)
            initial_locations[drone.id] = location
        self._record_snapshot(0, initial_locations)

        for turn in range(1, max_turn + 1):
            turn_moves: list[str] = []
            current_locations: dict[int, str] = {}
            for drone in self.drones:
                action, location = self._get_drone_action(drone, turn)
                current_locations[drone.id] = location
                if action is not None:
                    turn_moves.append(action)
            if turn_moves:
                print(" ".join(turn_moves))

            self._record_snapshot(turn, current_locations)

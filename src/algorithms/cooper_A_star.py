"""Implementation Cooperative A* pathfinding algorithm."""

import heapq
from collections import deque
from ..models import Graph, ZoneType
from .collision_manager import CollisionManager


class CooperativeAStar:
    """Plan collision-free routes for drones with A* search."""

    def __init__(
        self, graph: Graph, collision_manager: CollisionManager,
        max_turns: int = 1000
    ) -> None:
        """Set up route search with a graph and collision manager."""
        self.graph = graph
        self.cm = collision_manager
        self.max_turns = max_turns
        self.distances = self._calculate_static_distances(
            graph.end_zone_name
        )
        if graph.start_zone_name not in self.distances:
            raise ValueError(
                f"No valid path from '{graph.start_zone_name}' "
                f"to '{graph.end_zone_name}'."
            )

    def _calculate_static_distances(
        self, target_zone: str
    ) -> dict[str, float]:
        """Calculates minimum hops from target_zone to
        all other zones using simple BFS."""
        distances: dict[str, float] = {target_zone: 0.0}
        queue = deque([target_zone])
        # print(f"queue => {queue}")

        while queue:
            current = queue.popleft()
            # print(f"current => {current}")

            for neighbor, _, _ in self.graph.get_neighbors(current):
                # print(f"neighbor => {neighbor}")
                if neighbor.name not in distances:
                    distances[neighbor.name] = distances[current] + 1.0
                    queue.append(neighbor.name)

        return distances

    def _heuristic(self, zone_a: str) -> float:
        """Returns the precalculated minimum hops to the target zone."""
        return self.distances.get(zone_a, float("inf"))

    def _generate_valid_neighbors(
        self, current_zone: str, turn: int,
        g_cost: float, path: list[tuple[str, int]]
    ) -> list[tuple[float, float, int, str, list[tuple[str, int]]]]:
        """Create valid wait and move options from the current state."""
        neighbors = []
        next_turn = turn + 1
        is_free = self.cm.is_zone_free(current_zone, next_turn)

        if is_free:
            new_g = g_cost + 1.0
            new_f = new_g + self._heuristic(current_zone)
            new_path = path + [(current_zone, next_turn)]
            neighbors.append((new_f, new_g, next_turn, current_zone, new_path))

        for (
            neighbors_zone, conn, cost
        ) in self.graph.get_neighbors(current_zone):
            arrival_turn = turn + cost

            is_zone_free = self.cm.is_zone_free(
                neighbors_zone.name, arrival_turn
            )
            is_link_free = all(
                self.cm.is_link_free(conn, t)
                for t in range(turn + 1, arrival_turn + 1)
            )

            if is_zone_free and is_link_free:
                move_g = g_cost + float(cost)
                priority_bonus = 0.0
                if neighbors_zone.zone_type == ZoneType.PRIORITY:
                    priority_bonus = 0.001
                else:
                    priority_bonus = 0.0
                move_f = (move_g + self._heuristic(neighbors_zone.name)
                          - priority_bonus)
                move_path = path + [(neighbors_zone.name, arrival_turn)]
                neighbors.append((move_f, move_g, arrival_turn,
                                  neighbors_zone.name, move_path))

        return neighbors

    def plan_route(
        self, start_zone_name: str,
        end_zone_name: str, start_turn: int = 0
    ) -> list[tuple[str, int]] | None:
        """Finds a collision-free path for a single
        drone starting at start_turn."""
        f_score = self._heuristic(start_zone_name)
        start_path = [(start_zone_name, start_turn)]

        count = 0
        open_set: list[
            tuple[float, int, float, int, str, list[tuple[str, int]]]
        ] = [
            (f_score, count, 0.0, start_turn, start_zone_name, start_path)
        ]

        visited: set[tuple[str, int]] = set()

        i = 0
        while open_set:
            i = i + 1
            # print(f"open_set {i} turn =========> {open_set}")
            f_score, _, g_cost, turn, current_zone, path = heapq.heappop(
                open_set)

            state_key = (current_zone, turn)
            if state_key in visited:
                continue
            visited.add(state_key)

            if turn >= self.max_turns:
                continue

            if current_zone == end_zone_name:
                return path

            next_options = self._generate_valid_neighbors(
                current_zone, turn, g_cost, path
            )

            for next_f, next_g, next_turn, zone, new_path in next_options:
                count += 1
                heapq.heappush(
                    open_set,
                    (next_f, count, next_g, next_turn, zone, new_path),
                )

        return None

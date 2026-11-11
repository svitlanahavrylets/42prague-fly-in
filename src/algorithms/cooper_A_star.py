import heapq
from ..models.graph import Graph
from .collision_manager import CollisionManager

class CooperativeAStar:
    def __init__(
        self,
        graph: Graph,
        collision_manager: CollisionManager,
        max_turns: int = 500
    ) -> None:
        self.graph = graph
        self.cm = collision_manager
        self.max_turns = max_turns

    def _heuristic(self, zone_a: str, zone_end: str) -> float:
        zone_a = self.graph.zones[zone_a]
        zone_end = self.graph.zones[zone_end]
        h = abs(zone_a.x - zone_end.x) + abs(zone_a.y - zone_end.y)
        return float(h)

    def _generate_valid_neighbors(
        self,
        current_zone: str,
        turn: int,
        g_cost: float,
        target_zone: str,
        path: list[tuple[str, int]]
    ) -> list[tuple[float, float, int, str, list[tuple[str, int]]]]:
        neighbors = []
        next_turn = turn + 1
        is_free = self.cm.is_zone_free(current_zone, next_turn)

        if is_free:
            new_g = g_cost + 1.0
            new_f = new_g + self._heuristic(current_zone, target_zone)
            new_path = path + [(current_zone, next_turn)]
            neighbors.append((new_f, new_g, next_turn, current_zone, new_path))

        for neighbors_zone, conn, cost in self.graph.get_neighbors(current_zone):
            arrival_turn = turn + cost

            is_zone_free = self.cm.is_zone_free(neighbors_zone.name, turn + cost)
            is_link_free = self.cm.is_link_free(conn,  turn + 1)
            # print(f"neighbors_zone {neighbors_zone}, conn {conn}, cost{cost}")

            if is_zone_free and is_link_free:
                move_g = g_cost + float(cost)
                move_f = move_g + self._heuristic(neighbors_zone.name, target_zone)
                move_path = path + [(neighbors_zone.name, arrival_turn)]
                neighbors.append((move_f, move_g, arrival_turn, neighbors_zone.name, move_path))
        
        return neighbors

    def plan_route(
        self,
        start_zone_name: str,
        end_zone_name: str
    ) -> list[tuple[str, int]] | None:
        """Finds a collision-free path for a single drone 
        from start_zone_name to end_zone_name."""
        f_score = self._heuristic(start_zone_name, end_zone_name)
        start_path = [(start_zone_name, 0)]

        count = 0
        open_set: list[
            tuple[float, float, int, str, list[tuple[str, int]]]
        ] = [
        (f_score, count, 0.0, 0, start_zone_name, start_path)
        ]

        visited: set[tuple[str, int]] = set()

        i = 0
        while open_set:
            i = i + 1
            print(f"open_set {i} turn =========> {open_set}")
            f_score, _, g_cost, turn, current_zone, path = heapq.heappop(open_set)
            print(f"in open_set {i} current_zone =========> {current_zone}")
            print(f"in open_set {i} turn =========> {turn}")

            state_key = (current_zone, turn)
            if state_key in visited:
                continue
            visited.add(state_key)

            if turn >= self.max_turns:
                continue

            if current_zone == end_zone_name:
                return path

            next_options = self._generate_valid_neighbors(
                current_zone, turn, g_cost, end_zone_name, path
            )

            for next_f, next_g, next_turn, zone, new_path in next_options:
                count += 1
                heapq.heappush(
                    open_set,
                    (next_f, count, next_g, next_turn, zone, new_path),
                )

        return None     






        


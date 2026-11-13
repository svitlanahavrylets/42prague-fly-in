from ..models import Graph
from ..models import Connection


class CollisionManager:
    """Manages space-time reservations for zones
    and connections across turns."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self._zone_occupancy: dict[tuple[str, int], int] = {}
        self._link_occupancy: dict[tuple[str, int], int] = {}

    def _get_connection_id(self, conn: Connection) -> str:
        """Helper to get a unique consistent string key for a connection."""
        z1, z2 = sorted(conn.zones)
        return f"{z1}-{z2}"

    def is_zone_free(self, zone_name: str, turn: int) -> bool:
        """Check if a zone has available capacity at a specific turn."""
        if zone_name not in self.graph.zones:
            raise ValueError(f"Zone {zone_name!r} does not exist in the graph")

        zone = self.graph.zones[zone_name]

        if zone.is_start or zone.is_end:
            return True

        current_count = self._zone_occupancy.get((zone_name, turn), 0)
        return current_count < zone.max_drones

    def is_link_free(self, connection: Connection, turn: int) -> bool:
        conn_id = self._get_connection_id(connection)

        current_count = self._link_occupancy.get((conn_id, turn), 0)
        return current_count < connection.max_link_capacity

    def reserve_zone(self, zone_name: str, turn: int) -> None:
        if self.is_zone_free(zone_name, turn):
            key = (zone_name, turn)
            self._zone_occupancy[key] = self._zone_occupancy.get(key, 0) + 1
        else:
            raise ValueError(f"Zone {zone_name} is occupied")

    def reserve_link(self, connection: Connection, turn: int) -> None:
        """Reserve a slot on a connection link at a specific turn."""
        conn_id = self._get_connection_id(connection)
        if self.is_link_free(connection, turn):
            key = (conn_id, turn)
            self._link_occupancy[key] = self._link_occupancy.get(key, 0) + 1
        else:
            raise ValueError(f"Connection {conn_id} is occupied")

    def register_path(self, path: list[tuple[str, int]]) -> None:
        """Registers all zones and links used in a path across time."""
        for i in range(len(path)):
            zone_name, turn = path[i]
            zone = self.graph.zones[zone_name]
            if not zone.is_start and not zone.is_end:
                self.reserve_zone(zone_name, turn)

            if i < len(path) - 1:
                next_zone_name, next_turn = path[i + 1]
                if zone_name != next_zone_name:
                    conn = self.graph.get_connection(zone_name, next_zone_name)
                    if conn:
                        for t in range(turn + 1, next_turn + 1):
                            self.reserve_link(conn, t)

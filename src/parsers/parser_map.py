# from pydantic import ValidationError
from pathlib import Path
from ..models import Graph
from ..models import Connection
from ..models import ZoneType, Zone


RED = "\033[91m"
RESET = "\033[0m"


class MapParser:
    def __init__(self, map_path: Path) -> None:
        self.map_path = map_path

    def parse_map(self) -> tuple[Graph, int]:
        data = self.read_map_file()
        parsed_data = self.parse_data(data)
        return parsed_data

    def read_map_file(self) -> str:
        if not self.map_path.exists():
            raise FileNotFoundError(f"Map file is not found: '{self.map_path}")
        with open(self.map_path, "r", encoding="utf-8") as f:
            data = f.read()
            return data

    def parse_data(self, data: str) -> tuple[Graph, int]:
        nb_drones: int = 0
        zones: dict[str, Zone] = {}
        connections: list[Connection] = []
        start_zone_name: str | None = None
        end_zone_name: str | None = None

        for l_index, line in enumerate(data.splitlines(), start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("nb_drones:"):
                try:
                    nb_drones = int(line.split(":")[1])
                    if nb_drones <= 0:
                        raise ValueError(
                            "Number of drones should be grather than 0"
                        )
                except ValueError as e:
                    raise ValueError(
                        f"Line {l_index}: Invalid drone count. {e}"
                    )
                continue

            if line.startswith(("start_hub:", "end_hub:", "hub:")):
                zone, is_start, is_end = self.parse_zone_line(line, l_index)

                if zone.name in zones:
                    raise ValueError(
                        f"Line {l_index}: Duplicate zone name '{zone.name}'"
                    )
                zones[zone.name] = zone

                if is_start:
                    if start_zone_name is not None:
                        raise ValueError(
                            f"Line {l_index}: Multiple start_hubs defined!"
                        )
                    start_zone_name = zone.name

                if is_end:
                    if end_zone_name is not None:
                        raise ValueError(
                            f"Line {l_index}: Multiple end_hubs defined!"
                        )
                    end_zone_name = zone.name

                continue

            if line.startswith("connection:"):
                conn = self.parse_connection_line(line, l_index, zones)

                for existing_conn in connections:
                    same_order = (
                        existing_conn.zones[0] == conn.zones[0]
                        and existing_conn.zones[1] == conn.zones[1]
                    )
                    reverse_order = (
                        existing_conn.zones[0] == conn.zones[1]
                        and existing_conn.zones[1] == conn.zones[0]
                    )
                    if same_order or reverse_order:
                        raise ValueError(
                            f"Line {l_index}: Duplicate connection "
                            f"'{conn.zones[0]}-{conn.zones[1]}'"
                        )

                connections.append(conn)
                continue

        if start_zone_name is None:
            raise ValueError("Missing start zone")
        if end_zone_name is None:
            raise ValueError("Missing end zone")

        graph = Graph(
            zones=zones,
            connections=connections,
            start_zone_name=start_zone_name,
            end_zone_name=end_zone_name,
        )
        return graph, nb_drones

    def parse_zone_line(
        self,
        line: str,
        l_index: int,
    ) -> tuple[Zone, bool, bool]:
        is_start = line.startswith("start_hub:")
        is_end = line.startswith("end_hub:")

        if "[" in line or "]" in line:
            if (
                line.count("[") != 1
                or line.count("]") != 1
                or line.find("[") > line.find("]")
                or not line.rstrip().endswith("]")
            ):
                raise ValueError(f"Line {l_index}: Invalid metadata "
                                 f"block syntax or extra text after ']'")

        content = line.split(":", 1)[1].strip()

        metadata: dict[str, str] = {}
        if "[" in content and "]" in content:
            main_part, meta_part = content.split("[", 1)
            meta_str = meta_part.rstrip("]").strip()

            for item in meta_str.split():
                if "=" in item:
                    k, v = item.split("=", 1)
                    metadata[k] = v
            content = main_part.strip()

        parts = content.split()
        if len(parts) < 3:
            raise ValueError(f"Line {l_index}: Invalid zone line format."
                             f" Missing data for Zone")
        if len(parts) > 3:
            raise ValueError(f"Line {l_index}: Invalid zone line format. "
                             f"Extra data found: '{' '.join(parts[3:])}'")
        name = parts[0]

        if "-" in name:
            raise ValueError(f"Line {l_index}: Zone name '{name}' "
                             f"cannot contain dashes ('-')")
        try:
            x_zone = int(parts[1])
            y_zone = int(parts[2])
        except ValueError:
            raise ValueError(
                f"Line {l_index}: Coordinates X and Y must be integers. "
                f"Got '{parts[1]}', '{parts[2]}'."
            )

        zone_type_str = metadata.get("zone", "normal").upper()
        try:
            zone_type = ZoneType[zone_type_str]
        except KeyError:
            raise ValueError(
                f"Line {l_index}: Unknown zone type '{zone_type_str}'"
            )
        try:
            max_drones = int(metadata.get("max_drones", 1))
        except ValueError:
            raise ValueError(
                f"Line {l_index}: 'max_drones' must be an integer"
            )
        color = metadata.get("color", None)

        zone = Zone(
            name=name,
            x=x_zone,
            y=y_zone,
            zone_type=zone_type,
            max_drones=max_drones,
            color=color,
            is_start=is_start,
            is_end=is_end,
        )

        return zone, is_start, is_end

    def parse_connection_line(
        self, line: str, l_index: int, zones: dict[str, Zone]
    ) -> Connection:
        content = line.split(":", 1)[1].strip()

        metadata: dict[str, str] = {}
        if "[" in content and "]" in content:
            main_part, meta_part = content.split("[", 1)
            meta_str = meta_part.rstrip("]").strip()
            for item in meta_str.split():
                if "=" in item:
                    k, v = item.split("=", 1)
                    metadata[k] = v
            content = main_part.strip()

        parts = content.split("-")
        if len(parts) != 2:
            raise ValueError(
                f"Line {l_index}: Connection format must be 'zone1-zone2'"
            )

        z1_name, z2_name = parts[0].strip(), parts[1].strip()

        if z1_name not in zones:
            raise ValueError(
                f"Line {l_index}: Connection refers to undefined zone "
                f"'{z1_name}'"
            )
        if z2_name not in zones:
            raise ValueError(
                f"Line {l_index}: Connection refers to undefined zone "
                f"'{z2_name}'"
            )

        max_capacity = int(metadata.get("max_link_capacity", 1))

        connection = Connection(
            zones=(z1_name, z2_name),
            max_link_capacity=max_capacity
        )
        return connection

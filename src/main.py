import sys
import argparse
from pathlib import Path
from src.parsers.parser_map import MapParser
from src.models.drone import Drone
from src.algorithms.collision_manager import CollisionManager
from src.algorithms.cooper_A_star import CooperativeAStar

RED = "\033[91m"
RESET = "\033[0m"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fly-in: Drone routing simulation"
    )
    parser.add_argument(
        "map",
        nargs="?",
        type=Path,
        default=Path("my_maps/example.txt"),
        help="Path to the default map (my_maps/example.txt)"

    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()

    try:
        print(f"Loading map from: {args.map}")
        parser = MapParser(args.map)
        graph, nb_drones = parser.parse_map()

        drones = Drone.create_fleet(nb_drones, graph.start_zone_name)
        print(f"drones => {drones}")
        cm = CollisionManager(graph)
        algorithms = CooperativeAStar(graph, cm)

        for drone in drones:
            print(f"drone => {drone}")
            
            start_turn = 0
            path = algorithms.plan_route(
                start_turn, graph.start_zone_name, graph.end_zone_name
            )
            print(f"path => {path}")
            if path is None:
                raise ValueError(f"Path for Drone {drone.id!r} does not exist")
                break

            drone.path = path
            cm.register_path(path)
            print(f"✅ {drone.id}: {path}")

    except FileNotFoundError as e:
        print(f"{RED}Error: Map file not found. "
              f"{e}.{RESET}", file=sys.stderr
        )
        sys.exit(1)
    except ValueError as e:
        print(f"{RED}Map Format Error: "
              f"{e}.{RESET}", file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(f"{RED}Unexpected Error: {e}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
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
        print("\n------------algorithms-----------")
        algorithms = CooperativeAStar(graph, cm, )

        cas = algorithms._heuristic("hub", "goal")
        print(f" def _heuristic => {cas}")

        generate_neib = algorithms._generate_valid_neighbors(
            graph.start_zone_name,
            0,
            0.0,
            graph.end_zone_name,
            [(graph.start_zone_name, 0)]
        )

        print("\n------------def _generate_valid_neighbors(-----------")
        print(f"{generate_neib}")
        print("\n--- generated neighbors path ---")
        for item in generate_neib:
            f_score, g_cost, turn, zone, path = item
            print(f"Zone: {zone}, Turn: {turn}, f_cost: {f_score}, Path: {path}")

        print(f"\n----------plan_route--------------")
        plan_route = algorithms.plan_route(graph.start_zone_name, graph.end_zone_name)
        print(f" plan_route => {plan_route}")

        print(f"\n-------------before-----------")
        print(f"is_free roof1 in turn 1 => {cm.is_zone_free('roof1', 1)}")
        print(f"_zone_occupancy => {cm._zone_occupancy.get(('roof1', 1), 0)}")
        print()
        print(f"reserve_zone => {cm.reserve_zone('roof1', 1)}")
        print(f"is_free roof1 in turn 1 after reservation => {cm.is_zone_free('roof1', 1)}")
        print(f"_zone_occupancy after reservation => {cm._zone_occupancy.get(('roof1', 1), 0)}")
        print()
        print(f"reserve_zone => {cm.reserve_zone('roof1', 1)}")
        print(f"is_free roof1 in turn 1 again => {cm.is_zone_free('roof1', 1)}")
        print(f"is_free roof1 in turn 2 after reservation => {cm.is_zone_free('roof1', 2)}")
        print(f"_zone_occupancy after reservation => {cm._zone_occupancy.get(('roof1', 2), 0)}")
        print()






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
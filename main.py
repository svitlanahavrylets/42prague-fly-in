import sys
import traceback

from src.parsers import MapParser
from src.parsers import ArgParser
from src.models import Drone
from src.algorithms import CollisionManager
from src.algorithms import CooperativeAStar
from src.controllers import SimulationController

RED = "\033[91m"
RESET = "\033[0m"

def main() -> None:

    try:
        args = ArgParser.parse_args()
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
            if path is None:
                raise ValueError(f"Path for Drone {drone.id!r} does not exist")
                break

            drone.path = path
            cm.register_path(path)
            print(f"✅ {drone.id}: {path}")

        print("----------simulations-----------")
        controller = SimulationController(drones)
        controller.run()

        if args.visual == "pygame":
            from src.visualizers.pygame_visualizer import PygameVisualizer

            visualizer = PygameVisualizer(graph, controller.history)
            visualizer.render()

    except FileNotFoundError as e:
        print(
            f"{RED}Error: Map file not found. {e}.{RESET}",
            file=sys.stderr,
        )
        traceback.print_exc()
        sys.exit(1)
    except ValueError as e:
        print(
            f"{RED}Map Format Error: {e}.{RESET}",
            file=sys.stderr,
        )
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"{RED}Unexpected Error: {e}{RESET}",
            file=sys.stderr,
        )
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

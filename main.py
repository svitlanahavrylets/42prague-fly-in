import sys
import os
# import traceback

from src.parsers import MapParser, ArgParser
from src.models import Drone
from src.algorithms import CollisionManager, CooperativeAStar
from src.controllers import SimulationController
from src.visualizers.base import VisualizationError

RED = "\033[91m"
RESET = "\033[0m"


def main() -> None:
    """Parse the input map, plan drone routes, and run the simulation."""

    try:
        args = ArgParser.parse_args()
        # print(f"Loading map from: {args.map}")
        parser = MapParser(args.map)
        graph, nb_drones = parser.parse_map()

        drones = Drone.create_fleet(nb_drones, graph.start_zone_name)
        # print(f"drones => {drones}")
        cm = CollisionManager(graph)
        algorithms = CooperativeAStar(graph, cm)

        for drone in drones:
            # print(f"drone => {drone}")

            path = algorithms.plan_route(
                graph.start_zone_name, graph.end_zone_name
            )
            if path is None:
                raise ValueError(f"Path for Drone {drone.id!r} does not exist")

            drone.path = path
            cm.register_path(path)
            # print(f"✅ {drone.id}: {path}")

        # print("----------simulations-----------")
        controller = SimulationController(drones)
        controller.run()

        if args.visual == "pygame":
            os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
            from src.visualizers.pygame_visualizer import PygameVisualizer

            visualizer = PygameVisualizer(
                graph, controller.history, nb_drones
            )
            visualizer.render()

    except FileNotFoundError as e:
        print(f"{RED}Error: Map file not found. {e}.{RESET}",
              file=sys.stderr)
        # traceback.print_exc()
        sys.exit(1)
    except ValueError as e:
        print(f"{RED}Map Format Error: {e}.{RESET}",
              file=sys.stderr)
        # traceback.print_exc()
        sys.exit(1)
    except VisualizationError as e:
        print(f"{RED}Visualization Error: {e}{RESET}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"{RED}Unexpected Error: {e}{RESET}",
              file=sys.stderr)
        # traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

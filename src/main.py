import sys
import argparse
from pathlib import Path
from src.parsers.parser_map import MapParser

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
        graph, nb_drones = parser.parse()

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
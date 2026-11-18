import argparse

from pathlib import Path

class ArgParser:
    """Read the command-line options for the simulation."""

    @staticmethod
    def parse_args() -> argparse.Namespace:
        """Return the parsed map path and visualization choice."""
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
        parser.add_argument(
            "--visual",
            choices=["cli", "pygame"],
            default="cli",
            help="Select the visual to use",
        )
        return parser.parse_args()

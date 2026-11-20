from abc import ABC

from ..models import Graph
from ..controllers import TurnSnapshot


class BaseVisualizer(ABC):
    """Abstract base class defining the interface
    for simulation visualizers."""

    def __init__(self, graph: Graph, history: list[TurnSnapshot]) -> None:
        """Initialize the visualizer with a graph and simulation history."""
        self._graph: Graph = graph
        self._history: list[TurnSnapshot] = history

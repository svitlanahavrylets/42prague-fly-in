import sys
import pygame

from ..controllers import TurnSnapshot
from ..models import Graph, Zone
from .base import BaseVisualizer
from .colors import ColorResolver, ThemePalette


class PygameVisualizer(BaseVisualizer):
    """Interactive 2D graphical visualizer for drone routing simulations."""

    WIDTH: int = 1280
    HEIGHT: int = 800
    PADDING_X: int = 120
    PADDING_TOP: int = 110
    PADDING_BOTTOM: int = 90
    FPS: int = 60

    def __init__(self, graph: Graph, history: list[TurnSnapshot]) -> None:
        """Initialize window parameters, palette, and precompute coordinates."""
        super().__init__(graph, history)
        self._palette: ThemePalette = ThemePalette()
        self._coords: dict[str, tuple[float, float]] = (
            self._compute_screen_coords()
        )
        self._font_small: pygame.font.Font | None = None
        self._font_hud: pygame.font.Font | None = None

    def _compute_screen_coords(self) -> dict[str, tuple[float, float]]:
        """Map graph (x, y) coordinates proportionally onto screen pixels."""
        zones: list[Zone] = list(self._graph.zones.values())
        if not zones:
            return {}

        xs = [z.x for z in zones]
        ys = [z.y for z in zones]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        span_x = max_x - min_x
        span_y = max_y - min_y

        avail_w = self.WIDTH - 2 * self.PADDING_X
        avail_h = self.HEIGHT - self.PADDING_TOP - self.PADDING_BOTTOM

        scale_x = avail_w / span_x if span_x > 0 else float("inf")
        scale_y = avail_h / span_y if span_y > 0 else float("inf")
        scale = min(scale_x, scale_y)
        if scale == float("inf"):
            scale = 1.0

        used_w = span_x * scale
        used_h = span_y * scale
        offset_x = self.PADDING_X + (avail_w - used_w) / 2.0
        offset_y = self.PADDING_TOP + (avail_h - used_h) / 2.0

        coords: dict[str, tuple[float, float]] = {}
        for zone in zones:
            sx = (
                offset_x + (zone.x - min_x) * scale
                if span_x > 0
                else self.WIDTH / 2.0
            )
            sy = (
                offset_y + (zone.y - min_y) * scale
                if span_y > 0
                else self.PADDING_TOP + avail_h / 2.0
            )
            coords[zone.name] = (sx, sy)
        return coords

    def _draw_grid(self, screen: pygame.Surface) -> None:
        """Draw a subtle background grid."""
        screen.fill(self._palette.background)
        step = 40
        for x in range(0, self.WIDTH, step):
            pygame.draw.line(
                screen, self._palette.grid, (x, 0), (x, self.HEIGHT), 1
            )
        for y in range(0, self.HEIGHT, step):
            pygame.draw.line(
                screen, self._palette.grid, (0, y), (self.WIDTH, y), 1
            )

    def _draw_connections(self, screen: pygame.Surface) -> None:
        """Draw edges between connected zones."""
        for conn in self._graph.connections:
            pos_a = self._coords.get(conn.zones[0])
            pos_b = self._coords.get(conn.zones[1])
            if pos_a is None or pos_b is None:
                continue

            width = 5 if conn.max_link_capacity > 1 else 3
            pygame.draw.line(
                screen,
                self._palette.connection_idle,
                (int(pos_a[0]), int(pos_a[1])),
                (int(pos_b[0]), int(pos_b[1])),
                width,
            )

    def _draw_zones(self, screen: pygame.Surface) -> None:
        """Draw zone hubs with colors and visual indicators for zone types."""
        for zone in self._graph.zones.values():
            pos = self._coords.get(zone.name)
            if pos is None:
                continue

            cx, cy = int(pos[0]), int(pos[1])
            is_terminal = zone.name in (
                self._graph.start_zone_name,
                self._graph.end_zone_name,
            )
            radius = 28 if is_terminal else 22

            z_type = zone.zone_type.value.lower()
            if "blocked" in z_type:
                fill_color = self._palette.blocked_hub
            else:
                fill_color = ColorResolver.resolve(zone.color)

            pygame.draw.circle(screen, fill_color, (cx, cy), radius)

            border_color = self._palette.text_primary
            if "priority" in z_type:
                border_color = self._palette.priority_border
            elif "restricted" in z_type:
                border_color = self._palette.restricted_border

            pygame.draw.circle(screen, border_color, (cx, cy), radius, 3)

            if is_terminal:
                pygame.draw.circle(
                    screen, self._palette.special_ring, (cx, cy), radius + 5, 2
                )

            if "blocked" in z_type:
                offset = radius // 2
                pygame.draw.line(
                    screen,
                    self._palette.restricted_border,
                    (cx - offset, cy - offset),
                    (cx + offset, cy + offset),
                    3,
                )
                pygame.draw.line(
                    screen,
                    self._palette.restricted_border,
                    (cx - offset, cy + offset),
                    (cx + offset, cy - offset),
                    3,
                )

            if self._font_small is not None:
                label = self._font_small.render(
                    zone.name, True, self._palette.text_primary
                )
                label_rect = label.get_rect(center=(cx, cy + radius + 16))
                screen.blit(label, label_rect)

    def render(self) -> None:
        """Start the Pygame window loop and render the simulation."""
        try:
            pygame.init()
            screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
            pygame.display.set_caption("Fly-in: Drone Routing Visualizer")
            clock = pygame.time.Clock()
            self._font_small = pygame.font.SysFont("consolas", 14)
            self._font_hud = pygame.font.SysFont("consolas", 18, bold=True)
        except pygame.error as exc:
            print(f"Pygame initialization error: {exc}", file=sys.stderr)
            return

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_ESCAPE
                ):
                    running = False

            self._draw_grid(screen)
            self._draw_connections(screen)
            self._draw_zones(screen)
            pygame.display.flip()
            clock.tick(self.FPS)

        pygame.quit()
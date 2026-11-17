import math
import os
import sys

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame  # noqa: E402

from ..controllers import TurnSnapshot
from ..models import Graph, Zone
from .base import BaseVisualizer
from .colors import ColorResolver, ThemePalette


class PygameVisualizer(BaseVisualizer):
    """Interactive 2D graphical visualizer for drone routing simulations."""

    DEFAULT_WIDTH: int = 1440
    DEFAULT_HEIGHT: int = 800
    PADDING_X: int = 95
    PADDING_TOP: int = 115
    PADDING_BOTTOM: int = 95
    FPS: int = 60

    def __init__(self, graph: Graph, history: list[TurnSnapshot]) -> None:
        """Initialize window parameters, animation state, and coordinates."""
        super().__init__(graph, history)
        self._palette: ThemePalette = ThemePalette()
        self._width: int = self.DEFAULT_WIDTH
        self._height: int = self.DEFAULT_HEIGHT
        self._coords: dict[str, tuple[float, float]] = (
            self._compute_screen_coords()
        )
        self._font_small: pygame.font.Font | None = None
        self._font_drone: pygame.font.Font | None = None
        self._font_title: pygame.font.Font | None = None

        self._turn_idx: int = 0
        self._progress: float = 0.0
        self._paused: bool = False
        self._speed: float = 1.0

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

        avail_w = max(100, self._width - 2 * self.PADDING_X)
        avail_h = max(100, self._height - self.PADDING_TOP - self.PADDING_BOTTOM)

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
                else self._width / 2.0
            )
            sy = (
                offset_y + (zone.y - min_y) * scale
                if span_y > 0
                else self.PADDING_TOP + avail_h / 2.0
            )
            coords[zone.name] = (sx, sy)
        return coords

    def _resolve_location_point(self, location: str) -> tuple[float, float]:
        """Return screen (x, y) for a zone name or a 'zoneA-zoneB' transit."""
        if location in self._coords:
            return self._coords[location]

        if "-" in location:
            part_a, part_b = location.split("-", 1)
            pos_a = self._coords.get(part_a)
            pos_b = self._coords.get(part_b)
            if pos_a is not None and pos_b is not None:
                return (
                    (pos_a[0] + pos_b[0]) / 2.0,
                    (pos_a[1] + pos_b[1]) / 2.0,
                )
        return (self._width / 2.0, self._height / 2.0)

    def _get_type_ring_color(
        self, zone_name: str, z_type: str
    ) -> tuple[int, int, int] | None:
        """Return accent ring color for special zones, or None for normal."""
        if zone_name == self._graph.start_zone_name:
            return self._palette.ring_start
        if zone_name == self._graph.end_zone_name:
            return self._palette.ring_end
        if "priority" in z_type:
            return self._palette.ring_priority
        if "restricted" in z_type:
            return self._palette.ring_restricted
        if "blocked" in z_type:
            return self._palette.ring_blocked
        return None

    def _draw_zone_node(
        self,
        screen: pygame.Surface,
        cx: int,
        cy: int,
        radius: int,
        fill_color: tuple[int, int, int],
        type_color: tuple[int, int, int] | None,
        is_blocked: bool,
    ) -> None:
        """Draw a zone node: clean circle for normal, ringed for special."""
        fill_radius = max(1, int(radius * 0.75))
        pygame.draw.circle(screen, fill_color, (cx, cy), fill_radius)

        if is_blocked:
            offset = max(2, fill_radius // 2)
            pygame.draw.line(
                screen,
                self._palette.ring_white,
                (cx - offset, cy - offset),
                (cx + offset, cy + offset),
                2,
            )
            pygame.draw.line(
                screen,
                self._palette.ring_white,
                (cx - offset, cy + offset),
                (cx + offset, cy - offset),
                2,
            )

        pygame.draw.circle(
            screen, self._palette.ring_white, (cx, cy), fill_radius + 1, 2
        )

        if type_color is not None:
            pygame.draw.circle(screen, type_color, (cx, cy), radius + 8, 5)
            pygame.draw.circle(
                screen, self._palette.ring_white, (cx, cy), radius + 11, 1
            )

    def _draw_grid(self, screen: pygame.Surface) -> None:
        """Draw a subtle background grid."""
        screen.fill(self._palette.background)
        step = 40
        for x in range(0, self._width, step):
            pygame.draw.line(
                screen, self._palette.grid, (x, 0), (x, self._height), 1
            )
        for y in range(0, self._height, step):
            pygame.draw.line(
                screen, self._palette.grid, (0, y), (self._width, y), 1
            )

    def _draw_connections(
        self,
        screen: pygame.Surface,
        current_snap: TurnSnapshot,
        next_snap: TurnSnapshot,
    ) -> None:
        """Draw connections and show progress on restricted transits."""
        transit_phases: dict[tuple[str, str], set[int]] = {}
        for drone_id, current_location in current_snap.drone_locations.items():
            next_location = next_snap.drone_locations.get(
                drone_id, current_location
            )
            if current_location == next_location:
                continue

            if "-" in next_location:
                connection_name = next_location
                phase = 1
            elif "-" in current_location:
                connection_name = current_location
                phase = 2
            else:
                continue

            zone_a, zone_b = connection_name.split("-", 1)
            if (
                zone_a not in self._graph.zones
                or zone_b not in self._graph.zones
            ):
                continue

            is_restricted_transit = any(
                self._graph.zones[zone_name].zone_type.value.lower()
                == "restricted"
                for zone_name in (zone_a, zone_b)
            )
            if is_restricted_transit:
                key = tuple(sorted((zone_a, zone_b)))
                transit_phases.setdefault(key, set()).add(phase)

        for conn in self._graph.connections:
            z1, z2 = conn.zones[0], conn.zones[1]
            pos_a = self._coords.get(z1)
            pos_b = self._coords.get(z2)
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

            phases = transit_phases.get(tuple(sorted((z1, z2))), set())
            if phases and self._font_drone is not None:
                mid_x = int((pos_a[0] + pos_b[0]) / 2.0)
                mid_y = int((pos_a[1] + pos_b[1]) / 2.0)

                badge_text = ", ".join(
                    f"{phase}/2" for phase in sorted(phases)
                )
                text_surf = self._font_drone.render(
                    badge_text, True, self._palette.connection_active
                )
                badge_rect = text_surf.get_rect(center=(mid_x, mid_y - 14))
                bg_rect = badge_rect.inflate(8, 4)
                pygame.draw.rect(
                    screen, self._palette.panel_bg, bg_rect, border_radius=4
                )
                screen.blit(text_surf, badge_rect)


    def _draw_zones(
        self, screen: pygame.Surface, snap: TurnSnapshot
    ) -> None:
        """Draw zone hubs, labels, and occupancy counters."""
        for zone in self._graph.zones.values():
            pos = self._coords.get(zone.name)
            if pos is None:
                continue

            cx, cy = int(pos[0]), int(pos[1])
            is_terminal = zone.name in (
                self._graph.start_zone_name,
                self._graph.end_zone_name,
            )
            radius = 22 if is_terminal else 16

            z_type = zone.zone_type.value.lower()
            is_blocked = "blocked" in z_type

            fill_color = (
                self._palette.blocked_hub
                if is_blocked
                else ColorResolver.resolve(zone.color)
            )
            type_color = self._get_type_ring_color(zone.name, z_type)

            self._draw_zone_node(
                screen, cx, cy, radius, fill_color, type_color, is_blocked
            )

            if self._font_small is not None:
                label = self._font_small.render(
                    zone.name, True, self._palette.text_primary
                )
                label_y = cy + radius + (20 if type_color is not None else 14)
                label_rect = label.get_rect(center=(cx, label_y))
                screen.blit(label, label_rect)

                if not is_blocked and self._font_drone is not None:
                    count = snap.zone_counts.get(zone.name, 0)
                    cap_str = (
                        f"{count}/∞"
                        if is_terminal
                        else f"{count}/{zone.max_drones}"
                    )
                    cap_color = (
                        self._palette.text_primary
                        if count > 0
                        else self._palette.text_muted
                    )
                    cap_surf = self._font_drone.render(
                        cap_str, True, cap_color
                    )
                    cap_y = cy - radius - (18 if type_color is not None else 13)
                    cap_rect = cap_surf.get_rect(center=(cx, cap_y))
                    screen.blit(cap_surf, cap_rect)

    def _draw_drones(self, screen: pygame.Surface) -> None:
        """Draw drones with smooth interpolation and multi-drone offsets."""
        if not self._history:
            return

        curr_snap = self._history[self._turn_idx]
        next_idx = min(self._turn_idx + 1, len(self._history) - 1)
        next_snap = self._history[next_idx]

        t = self._progress
        smooth_t = t * t * (3.0 - 2.0 * t)

        location_groups: dict[str, list[int]] = {}
        for drone_id, loc in next_snap.drone_locations.items():
            location_groups.setdefault(loc, []).append(drone_id)

        for drone_id in sorted(curr_snap.drone_locations.keys()):
            loc_a = curr_snap.drone_locations[drone_id]
            loc_b = next_snap.drone_locations.get(drone_id, loc_a)

            ax, ay = self._resolve_location_point(loc_a)
            bx, by = self._resolve_location_point(loc_b)

            group = location_groups.get(loc_b, [drone_id])
            if len(group) > 1:
                idx_in_group = group.index(drone_id)
                angle = (2.0 * math.pi * idx_in_group) / len(group)
                spread = 13.0
                bx += math.cos(angle) * spread
                by += math.sin(angle) * spread

            dx = int(ax + (bx - ax) * smooth_t)
            dy = int(ay + (by - ay) * smooth_t)

            pygame.draw.circle(screen, (248, 250, 252), (dx, dy), 11)
            pygame.draw.circle(screen, (15, 23, 42), (dx, dy), 11, 2)

            if self._font_drone is not None:
                id_surf = self._font_drone.render(
                    f"D{drone_id}", True, (15, 23, 42)
                )
                id_rect = id_surf.get_rect(center=(dx, dy))
                screen.blit(id_surf, id_rect)

    def _draw_top_legend(self, screen: pygame.Surface) -> None:
        """Draw a centered single-row legend bar at the top of the window."""
        legend_items: list[tuple[str, tuple[int, int, int] | None, bool]] = [
            ("Start", self._palette.ring_start, False),
            ("End", self._palette.ring_end, False),
            ("Priority", self._palette.ring_priority, False),
            ("Restricted", self._palette.ring_restricted, False),
            ("Normal", None, False),
            ("Blocked", self._palette.ring_blocked, True),
        ]

        item_spacing = 148
        total_w = len(legend_items) * item_spacing + 30
        panel_h = 48
        panel_x = (self._width - total_w) // 2
        panel_y = 16

        panel_rect = pygame.Rect(panel_x, panel_y, total_w, panel_h)
        pygame.draw.rect(
            screen, self._palette.panel_bg, panel_rect, border_radius=10
        )
        pygame.draw.rect(
            screen,
            self._palette.panel_border,
            panel_rect,
            width=1,
            border_radius=10,
        )

        center_y = panel_y + panel_h // 2
        for idx, (label_text, ring_color, is_blocked) in enumerate(
            legend_items
        ):
            icon_x = panel_x + 34 + idx * item_spacing
            fill = (
                self._palette.blocked_hub
                if is_blocked
                else self._palette.default_hub
            )
            self._draw_zone_node(
                screen=screen,
                cx=icon_x,
                cy=center_y,
                radius=5,
                fill_color=fill,
                type_color=ring_color,
                is_blocked=is_blocked,
            )

            if self._font_small is not None:
                text_surf = self._font_small.render(
                    label_text, True, self._palette.text_muted
                )
                text_rect = text_surf.get_rect(
                    midleft=(icon_x + 28, center_y)
                )
                screen.blit(text_surf, text_rect)

    def _draw_bottom_hud(
        self, screen: pygame.Surface, snap: TurnSnapshot
    ) -> None:
        """Draw bottom status and controls bar."""
        bar_w = min(1220, self._width - 40)
        bar_h = 48
        bar_x = (self._width - bar_w) // 2
        bar_y = self._height - bar_h - 18

        bar_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(
            screen, self._palette.panel_bg, bar_rect, border_radius=10
        )
        pygame.draw.rect(
            screen,
            self._palette.panel_border,
            bar_rect,
            width=1,
            border_radius=10,
        )

        total_turns = max(0, len(self._history) - 1)
        total_drones = len(snap.drone_locations)
        delivered = snap.zone_counts.get(self._graph.end_zone_name, 0)
        status = "PAUSED" if self._paused else "PLAYING"

        if self._font_small is not None:
            status_text = (
                f"Turn: {self._turn_idx}/{total_turns}   |   "
                f"Delivered: {delivered}/{total_drones}   |   "
                f"Speed: {self._speed:.1f}x [{status}]   ||   "
                "[SPACE] Pause  [LEFT/RIGHT] Step  [UP/DOWN] Speed  "
                "[R] Restart  [ESC] Quit"
            )
            hud_surf = self._font_small.render(
                status_text, True, self._palette.text_primary
            )
            hud_rect = hud_surf.get_rect(center=bar_rect.center)
            screen.blit(hud_surf, hud_rect)

    def _handle_keydown(self, key: int) -> bool:
        """Process keyboard controls. Return False to quit."""
        max_idx = max(0, len(self._history) - 1)
        if key == pygame.K_ESCAPE:
            return False
        if key == pygame.K_SPACE:
            if self._turn_idx >= max_idx and self._paused:
                self._turn_idx = 0
                self._progress = 0.0
            self._paused = not self._paused
        elif key == pygame.K_RIGHT:
            self._paused = True
            self._progress = 0.0
            self._turn_idx = min(max_idx, self._turn_idx + 1)
        elif key == pygame.K_LEFT:
            self._paused = True
            self._progress = 0.0
            self._turn_idx = max(0, self._turn_idx - 1)
        elif key == pygame.K_UP:
            self._speed = min(5.0, round(self._speed + 0.5, 1))
        elif key == pygame.K_DOWN:
            self._speed = max(0.5, round(self._speed - 0.5, 1))
        elif key == pygame.K_r:
            self._turn_idx = 0
            self._progress = 0.0
            self._paused = False
        return True

    def render(self) -> None:
        """Start the Pygame window loop and render the animated simulation."""
        if not self._history:
            print("No simulation history to render.", file=sys.stderr)
            return

        try:
            pygame.init()
            display_info = pygame.display.Info()
            if display_info.current_w > 0 and display_info.current_h > 0:
                self._width = int(display_info.current_w * 0.92)
                self._height = int(display_info.current_h * 0.85)
                self._coords = self._compute_screen_coords()

            screen = pygame.display.set_mode(
                (self._width, self._height), pygame.RESIZABLE
            )
            pygame.display.set_caption("Fly-in: Drone Routing Visualizer")
            clock = pygame.time.Clock()
            self._font_small = pygame.font.SysFont("consolas", 14)
            self._font_drone = pygame.font.SysFont("consolas", 11, bold=True)
            self._font_title = pygame.font.SysFont("consolas", 16, bold=True)
        except pygame.error as exc:
            print(f"Pygame initialization error: {exc}", file=sys.stderr)
            return

        try:
            running = True
            max_idx = len(self._history) - 1
            while running:
                dt = clock.tick(self.FPS) / 1000.0

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self._width = event.w
                        self._height = event.h
                        self._coords = self._compute_screen_coords()
                    elif event.type == pygame.KEYDOWN:
                        running = self._handle_keydown(event.key)

                if not self._paused and self._turn_idx < max_idx:
                    self._progress += dt * self._speed
                    if self._progress >= 1.0:
                        self._progress = 0.0
                        self._turn_idx += 1
                        if self._turn_idx >= max_idx:
                            self._paused = True

                current_snap = self._history[self._turn_idx]

                self._draw_grid(screen)
                next_snap = self._history[
                    min(self._turn_idx + 1, max_idx)
                ]
                self._draw_connections(screen, current_snap, next_snap)
                self._draw_zones(screen, current_snap)
                self._draw_drones(screen)
                self._draw_top_legend(screen)
                self._draw_bottom_hud(screen, current_snap)
                pygame.display.flip()
        except KeyboardInterrupt:
            pass
        finally:
            pygame.quit()

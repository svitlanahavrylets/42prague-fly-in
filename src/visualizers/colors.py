from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class ThemePalette:
    """Color constants for the Pygame visualization interface."""

    background: tuple[int, int, int] = (18, 20, 28)
    grid: tuple[int, int, int] = (28, 32, 44)
    text_primary: tuple[int, int, int] = (241, 245, 249)
    text_muted: tuple[int, int, int] = (148, 163, 184)
    hud_bg: tuple[int, int, int] = (15, 17, 24)

    default_hub: tuple[int, int, int] = (100, 116, 139)
    blocked_hub: tuple[int, int, int] = (51, 65, 85)
    priority_border: tuple[int, int, int] = (250, 204, 21)
    restricted_border: tuple[int, int, int] = (249, 115, 22)
    special_ring: tuple[int, int, int] = (226, 232, 240)

    connection_idle: tuple[int, int, int] = (71, 85, 105)
    connection_active: tuple[int, int, int] = (56, 189, 248)

    drone_fill: tuple[int, int, int] = (248, 250, 252)
    drone_border: tuple[int, int, int] = (15, 23, 42)
    drone_text: tuple[int, int, int] = (15, 23, 42)


class ColorResolver:
    """Safely converts zone metadata color strings into RGB tuples."""

    @staticmethod
    def resolve(color_name: str | None) -> tuple[int, int, int]:
        """Parse a color string into an (R, G, B) tuple
        with a safe fallback."""
        if not color_name:
            return ThemePalette.default_hub
        try:
            color = pygame.Color(color_name.strip())
            return (color.r, color.g, color.b)
        except ValueError:
            return ThemePalette.default_hub
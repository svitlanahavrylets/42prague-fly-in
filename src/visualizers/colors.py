from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class ThemePalette:
    """Color constants for the Pygame visualization."""

    background: tuple[int, int, int] = (18, 20, 28)
    grid: tuple[int, int, int] = (28, 32, 44)
    panel_bg: tuple[int, int, int] = (24, 28, 38)
    panel_border: tuple[int, int, int] = (45, 52, 70)

    text_primary: tuple[int, int, int] = (235, 240, 248)
    text_muted: tuple[int, int, int] = (148, 163, 184)

    default_hub: tuple[int, int, int] = (92, 103, 122)
    blocked_hub: tuple[int, int, int] = (55, 62, 75)

    ring_white: tuple[int, int, int] = (235, 240, 248)
    ring_start: tuple[int, int, int] = (74, 186, 122)
    ring_end: tuple[int, int, int] = (214, 86, 86)
    ring_priority: tuple[int, int, int] = (224, 184, 68)
    ring_restricted: tuple[int, int, int] = (0, 191, 255)
    ring_blocked: tuple[int, int, int] = (115, 125, 140)
    ring_normal: tuple[int, int, int] = (105, 138, 175)

    connection_idle: tuple[int, int, int] = (71, 85, 105)
    connection_active: tuple[int, int, int] = (56, 189, 248)


class ColorResolver:
    """Safely converts zone metadata color strings into muted RGB tuples."""

    @staticmethod
    def resolve(color_name: str | None) -> tuple[int, int, int]:
        """Parse a color string into a muted (R, G, B) tuple."""
        if not color_name:
            return ThemePalette.default_hub
        try:
            c = pygame.Color(color_name.strip())
            bg_r, bg_g, bg_b = ThemePalette.background
            muted_r = int(c.r * 0.65 + bg_r * 0.35)
            muted_g = int(c.g * 0.65 + bg_g * 0.35)
            muted_b = int(c.b * 0.65 + bg_b * 0.35)
            return (muted_r, muted_g, muted_b)
        except ValueError:
            return ThemePalette.default_hub

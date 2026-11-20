"""Color parsing, hue-shifted shading, and palette resolution utilities."""

from typing import Mapping

RGBA = tuple[int, int, int, int]
TRANSPARENT: RGBA = (0, 0, 0, 0)


def ground_shadow_color(color: RGBA) -> RGBA:
    """Keep ground shadows subtle while preserving an already lower alpha."""
    return (*color[:3], min(color[3], 64))


def parse_color(
    value: str | list[int] | tuple[int, ...],
    palette: Mapping[str, RGBA] | None = None,
) -> RGBA:
    """Parse a hex string, 'transparent', RGBA tuple/list, or palette key into RGBA."""
    if isinstance(value, (list, tuple)):
        if len(value) == 3:
            return (int(value[0]), int(value[1]), int(value[2]), 255)
        if len(value) == 4:
            return (int(value[0]), int(value[1]), int(value[2]), int(value[3]))
        raise ValueError(f"Invalid RGBA sequence: {value!r}")

    if not isinstance(value, str):
        raise ValueError(f"Unsupported color type: {type(value).__name__}")

    if palette and value in palette:
        return palette[value]

    lower = value.strip().lower()
    if lower in ("transparent", "none", ""):
        return TRANSPARENT

    hex_str = lower.lstrip("#")
    if len(hex_str) == 6:
        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
        return (r, g, b, 255)
    if len(hex_str) == 8:
        r, g, b, a = (
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16),
            int(hex_str[6:8], 16),
        )
        return (r, g, b, a)

    raise ValueError(f"Invalid color value: {value!r}")


def darken(c: RGBA, factor: float = 0.75) -> RGBA:
    """Darken an RGBA color with cool-purple pixel-art hue shifting."""
    r, g, b, a = c
    # Cool shift: red & green drop faster than blue so shadows lean indigo/violet
    nr = max(0, min(255, int(r * (factor * 0.94))))
    ng = max(0, min(255, int(g * (factor * 0.98))))
    nb = max(0, min(255, int(b * min(1.0, factor * 1.08) + 2)))
    return (nr, ng, nb, a)


def brighten(c: RGBA, factor: float = 1.16) -> RGBA:
    """Brighten an RGBA color with warm-sunlight pixel-art hue shifting."""
    r, g, b, a = c
    # Warm shift: red & green gain slightly more than blue so highlights lean golden
    nr = max(0, min(255, int(r * (factor * 1.04) + 8)))
    ng = max(0, min(255, int(g * (factor * 1.01) + 6)))
    nb = max(0, min(255, int(b * (factor * 0.95) + 3)))
    return (nr, ng, nb, a)


def nearest_palette_color(target: RGBA, palette: Mapping[str, RGBA]) -> RGBA:
    """Snap an RGBA color to the closest opaque color in `palette`."""
    candidates = [c for c in palette.values() if c[3] > 0]
    if not candidates:
        return target
    tr, tg, tb, ta = target
    best = min(
        candidates,
        key=lambda c: (c[0] - tr) ** 2 * 2 + (c[1] - tg) ** 2 * 4 + (c[2] - tb) ** 2 * 3,
    )
    return (best[0], best[1], best[2], ta)

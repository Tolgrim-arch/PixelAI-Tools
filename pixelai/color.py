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


def luminance(c: RGBA) -> float:
    """Return perceptual luminance in [0.0, 255.0]."""
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def lerp_rgba(a: RGBA, b: RGBA, t: float) -> RGBA:
    """Linearly interpolate between two RGBA colors."""
    t = max(0.0, min(1.0, t))
    return (
        max(0, min(255, int(round(a[0] + (b[0] - a[0]) * t)))),
        max(0, min(255, int(round(a[1] + (b[1] - a[1]) * t)))),
        max(0, min(255, int(round(a[2] + (b[2] - a[2]) * t)))),
        max(0, min(255, int(round(a[3] + (b[3] - a[3]) * t)))),
    )


def blend_add(base: RGBA, glow: RGBA, amount: float = 1.0) -> RGBA:
    """Additive blend preserving base alpha."""
    amt = max(0.0, amount)
    return (
        max(0, min(255, int(round(base[0] + glow[0] * amt)))),
        max(0, min(255, int(round(base[1] + glow[1] * amt)))),
        max(0, min(255, int(round(base[2] + glow[2] * amt)))),
        base[3],
    )


def blend_screen(base: RGBA, glow: RGBA, amount: float = 1.0) -> RGBA:
    """Screen blend preserving base alpha for soft luminous highlights."""
    amt = max(0.0, min(1.0, amount))
    sr = 255 - ((255 - base[0]) * (255 - glow[0])) // 255
    sg = 255 - ((255 - base[1]) * (255 - glow[1])) // 255
    sb = 255 - ((255 - base[2]) * (255 - glow[2])) // 255
    return lerp_rgba(base, (sr, sg, sb, base[3]), amt)


MATERIAL_PRESETS: dict[str, dict[str, object]] = {
    "gold_specular": {
        "ramp": ("#5c2e14", "#9e5516", "#d98b1e", "#ffd24a", "#fff7b8"),
        "reflectance": "metallic_specular",
        "outline": "#3b1d0d",
    },
    "silver_chrome": {
        "ramp": ("#2b3347", "#53627d", "#8ca0bd", "#cbd7e6", "#ffffff"),
        "reflectance": "metallic_specular",
        "outline": "#1b202e",
    },
    "bronze_aged": {
        "ramp": ("#3f261c", "#6e4228", "#a1663a", "#cf9155", "#f2c483"),
        "reflectance": "metallic_specular",
        "outline": "#291812",
    },
    "emerald_crystal": {
        "ramp": ("#103d2e", "#1d6e4a", "#32a866", "#74e08e", "#d6ffcf"),
        "reflectance": "crystalline",
        "outline": "#0b261d",
    },
    "ruby_enchanted": {
        "ramp": ("#4a1225", "#8a1c38", "#cf324e", "#ff6e78", "#ffd4d8"),
        "reflectance": "crystalline",
        "outline": "#2b0a16",
    },
    "amethyst_void": {
        "ramp": ("#291642", "#4e2878", "#8545bd", "#bd7ef2", "#f0d4ff"),
        "reflectance": "crystalline",
        "outline": "#170b26",
    },
    "frost_ice": {
        "ramp": ("#214b6e", "#3878a3", "#64b2d9", "#a8e4f5", "#f0fcff"),
        "reflectance": "crystalline",
        "outline": "#142f47",
    },
    "obsidian_dark": {
        "ramp": ("#161421", "#282438", "#433d5c", "#746c94", "#b5add6"),
        "reflectance": "metallic_specular",
        "outline": "#0c0a12",
    },
}


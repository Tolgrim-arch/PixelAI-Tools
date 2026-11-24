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


def _shift_hue_toward(h: float, target_h: float, strength: float) -> float:
    """Shift normalized hue `h` in [0, 1) toward `target_h` by `strength` in [0, 1]."""
    diff = (target_h - h + 0.5) % 1.0 - 0.5
    return (h + diff * strength) % 1.0


def darken(c: RGBA, factor: float = 0.75) -> RGBA:
    """Darken an RGBA color with cool-violet chromatic hue-shifting (never pure black)."""
    import colorsys

    r, g, b, a = c
    if a == 0:
        return c
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    step = max(0.0, min(1.0, 1.0 - factor))
    # Shift hue toward cool indigo/violet (~255 deg = 0.708)
    nh = _shift_hue_toward(h, 0.708, step * 0.32) if s > 0.05 else 0.708
    # Boost saturation slightly in shadows so they stay rich & chromatic, never muddy grey/black
    ns = min(0.92, max(s * (1.0 + step * 0.22), 0.16 if step > 0.15 else s))
    # Clamp minimum lightness so shadows never collapse to dead #000000
    nl = max(0.13, min(l, l * factor))
    nr, ng, nb = colorsys.hls_to_rgb(nh, nl, ns)
    return (int(round(nr * 255)), int(round(ng * 255)), int(round(nb * 255)), a)


def brighten(c: RGBA, factor: float = 1.16) -> RGBA:
    """Brighten an RGBA color with warm-sunlight chromatic hue-shifting (never pure white)."""
    import colorsys

    r, g, b, a = c
    if a == 0:
        return c
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    step = max(0.0, min(1.0, factor - 1.0))
    # Shift hue toward warm golden sunlight (~52 deg = 0.144)
    nh = _shift_hue_toward(h, 0.144, step * 0.35) if s > 0.05 else 0.125
    # Keep visible chroma so highlights stay luminous cream/gold/peach, never dead #ffffff
    ns = max(0.24, min(0.95, s * (1.0 - step * 0.12))) if s > 0.05 else 0.22
    # Clamp maximum lightness below pure white
    nl = min(0.87, max(l, l + (1.0 - l) * min(0.78, step * 0.75)))
    nr, ng, nb = colorsys.hls_to_rgb(nh, nl, ns)
    return (int(round(nr * 255)), int(round(ng * 255)), int(round(nb * 255)), a)


def specular_highlight(c: RGBA) -> RGBA:
    """Return a luminous warm-tinted specular highlight derived from `c` (never pure #ffffff)."""
    return brighten(c, 1.55)


def shade_ramp_dithered(
    ramp: list[RGBA],
    value: float,
    x: int,
    y: int,
    dither_strength: float = 0.28,
) -> RGBA:
    """Map `value` in [0, 1] to `ramp` (darkest..lightest) using 4x4 Bayer dithering at band edges."""
    if not ramp:
        return TRANSPARENT
    if len(ramp) == 1:
        return ramp[0]
    v = max(0.0, min(0.9999, value))
    scaled = v * (len(ramp) - 1)
    idx = int(scaled)
    frac = scaled - idx
    if dither_strength > 0.0 and idx < len(ramp) - 1:
        # Apply 4x4 Bayer dithering only within the transition strip around 0.5
        lo = 0.5 - dither_strength * 0.5
        hi = 0.5 + dither_strength * 0.5
        if lo < frac < hi:
            t = (frac - lo) / max(1e-6, hi - lo)
            if t > bayer_threshold(x, y):
                return ramp[idx + 1]
    return ramp[idx]


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


BAYER_4X4: tuple[float, ...] = tuple(
    (v + 0.5) / 16.0
    for v in (0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5)
)


def bayer_threshold(x: int, y: int) -> float:
    """Return the normalized 4x4 Bayer threshold in (0, 1) for pixel (x, y)."""
    return BAYER_4X4[((y & 3) << 2) | (x & 3)]


def dither_band_index(
    v: float, n: int, x: int, y: int, strip: float = 1.0 / 3.0
) -> int:
    """Map a normalized scalar `v` in [0, 1] to a palette index in [0, n-1].

    Keeps color bands flat and applies 4x4 Bayer ordered dithering only inside
    a thin transition strip of width `strip` where two bands meet.
    """
    if n <= 1:
        return 0
    clamped = max(0.0, min(1.0, v))
    f = clamped * (n - 1)
    k = int(f)
    if k >= n - 1:
        return n - 1
    fr = f - k
    if strip <= 0.0:
        return min(n - 1, k + (1 if fr >= 0.5 else 0))
    t = max(0.0, min(1.0, (fr - 0.5) / strip + 0.5))
    return min(n - 1, k + (1 if bayer_threshold(x, y) < t else 0))


def hsl_to_rgba(h: float, s: float, l: float, a: int = 255) -> RGBA:
    """Convert HSL (h in degrees, s and l in [0, 1]) to an RGBA tuple."""
    h_norm = (((h % 360.0) + 360.0) % 360.0) / 60.0
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    x = c * (1.0 - abs((h_norm % 2.0) - 1.0))
    m = l - c * 0.5
    if h_norm < 1.0:
        r, g, b = c, x, 0.0
    elif h_norm < 2.0:
        r, g, b = x, c, 0.0
    elif h_norm < 3.0:
        r, g, b = 0.0, c, x
    elif h_norm < 4.0:
        r, g, b = 0.0, x, c
    elif h_norm < 5.0:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    return (
        max(0, min(255, int(round((r + m) * 255.0)))),
        max(0, min(255, int(round((g + m) * 255.0)))),
        max(0, min(255, int(round((b + m) * 255.0)))),
        max(0, min(255, int(a))),
    )


def hue_ramp(
    n: int,
    hue: float = 110.0,
    shift: float = 60.0,
    sat: float = 0.55,
    sat_drop: float = 0.35,
    light: tuple[float, float] = (0.12, 0.62),
) -> list[RGBA]:
    """Build an n-step hue-shifted pixel art color ramp (shadows -> blue 240, lights -> yellow 60)."""
    if n <= 0:
        return []
    l0, l1 = float(light[0]), float(light[1])

    def _toward(h_deg: float, target: float, amt: float) -> float:
        diff = ((target - h_deg + 540.0) % 360.0) - 180.0
        sign = 1.0 if diff >= 0.0 else -1.0
        return h_deg + sign * min(abs(diff), amt)

    ramp: list[RGBA] = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.5
        edge = abs(2.0 * t - 1.0)
        h_val = _toward(hue, 240.0 if t < 0.5 else 60.0, shift * edge)
        s_val = max(0.0, min(1.0, sat * (1.0 - sat_drop * edge)))
        l_val = max(0.0, min(1.0, l0 + (l1 - l0) * t))
        ramp.append(hsl_to_rgba(h_val, s_val, l_val))
    return ramp



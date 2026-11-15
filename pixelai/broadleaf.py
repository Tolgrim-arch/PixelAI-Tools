"""Native-resolution broadleaf trees (oak, fruit) using the band + leaf-stamp method from leafstudy rows 2-3."""

import random
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color
from pixelai import foliage as fo
from pixelai import leafstudy as ls


def _draw_fruit(local: Canvas, fx: int, fy: int, r: int, base: RGBA, hi: RGBA, sh: RGBA, leaf: RGBA) -> None:
    """Shaded fruit: top-left highlight, bottom-right shade, tiny stem leaf."""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                local.set_pixel(fx + dx, fy + dy, hi if dx + dy < -r // 2 else sh if dx + dy > r // 2 else base)
    local.set_pixel(fx, fy - r - 1, leaf)


def _crown_bands(cx: int, cy: int, rx: int, ry: int) -> dict[tuple[int, int], int]:
    """Build multi-lobe crown with flat 4-band shading (0=light, 1=base, 2=shade, 3=deep) like leafstudy rows 2-3."""
    lobes = (
        (cx - int(rx * 0.42), cy - int(ry * 0.25), int(rx * 0.56)),
        (cx + int(rx * 0.36), cy - int(ry * 0.20), int(rx * 0.52)),
        (cx, cy - int(ry * 0.38), int(rx * 0.54)),
        (cx - int(rx * 0.48), cy + int(ry * 0.14), int(rx * 0.50)),
        (cx + int(rx * 0.46), cy + int(ry * 0.14), int(rx * 0.50)),
        (cx, cy + int(ry * 0.06), int(rx * 0.68)),
    )
    bands: dict[tuple[int, int], int] = {}
    # Paint back-to-front / bottom-to-top so upper-left lobes overlap cleanly
    for lx, ly, lr in lobes:
        disc = ls._disc_bands(lx, ly, lr, ls._L2, (-0.17, -0.2, 0.88), (-0.2, -0.2, 1.0))
        for p, b in disc.items():
            # Keep brighter band if already covered by an upper lobe, or overwrite from upper lobes
            if p not in bands or b < bands[p]:
                bands[p] = b
    return bands


def draw_broadleaf(canvas: Canvas, x: int, y: int, palette: dict[str, RGBA], op: dict[str, Any], frame: int = 0) -> None:
    """Draw an oak or fruit tree natively at (w, h); default 128x128."""
    w, h = int(op.get("w", 128)), int(op.get("h", 128))
    variant = str(op.get("variant", "oak")).lower()
    colors = [parse_color(c, palette) for c in op.get("band_colors", ls.BAND)]
    bark = fo.get_bark(op, palette)
    rng = random.Random(int(op.get("seed", 11 if variant == "oak" else 17)))
    local = Canvas(w, h)
    cx, foot = w // 2, h - 9
    if op.get("shadow", True):
        fo.draw_ground_shadow(local, cx, foot, w, parse_color(op.get("shadow_color", fo.SHADOW), palette))
    fo.draw_trunk(local, rng, cx, int(h * 0.44), foot, max(6, w // 9), bark)

    off = (-1, 0, 1, 0)[frame % 4] if op.get("sway") else 0
    rx, ry = int(w * 0.36), int(h * 0.28)
    cy = max(ry + 8, int(h * 0.38))
    bands = _crown_bands(cx + off, cy, rx, ry)
    stamped = ls._stamp(rng, bands, cx + off, cy, reach=9, fringe=0.55, long_from=None)
    for (px, py) in stamped:  # crown cast shadow on the trunk
        for d in (1, 2, 3, 4):
            q = (px, py + d)
            if q not in stamped and 0 <= q[0] < w and 0 <= q[1] < h and local.get_pixel(*q) in bark[1:]:
                local.set_pixel(q[0], q[1], bark[0])
    for (px, py), b in stamped.items():
        if 0 <= px < w and 0 <= py < h:
            local.set_pixel(px, py, colors[b])

    if variant == "fruit":
        accent = parse_color(op.get("accent_color", "#d94e41"), palette)
        r, placed = max(2, w // 40), 0
        for _ in range(80):
            if placed >= 7:
                break
            fx = cx + off + rng.randint(-int(rx * 0.65), int(rx * 0.65))
            fy = cy + rng.randint(-int(ry * 0.55), int(ry * 0.55))
            if all((fx + a, fy + b) in stamped for a, b in ((0, 0), (-r, -r), (r, r), (0, -r - 1))):
                _draw_fruit(local, fx, fy, r, accent, brighten(accent, 1.32), darken(accent, 0.68), colors[2])
                placed += 1
    canvas.blit(local, x, y)

"""Native-resolution broadleaf (oak & fruit) tree generator.

Follows the Blob -> Shape -> Shade method:
- Blob: wide, organic scalloped crown silhouette, despiked and single-island.
- Shape: top-left light model, deep underside & lower-right shade, 4-tone bark trunk with flared roots.
- Shade: clustered leaf tufts with lit/dark crescents, rim light/dark, shadow pockets, sun glints,
  and shaded fruit clusters for the 'fruit' variant.
"""

import math
import random
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color
from pixelai.conifer import _BARK, _NEEDLES, _SHADOW, _draw_trunk, _ramp, _shade_tier


def _crown_mask(
    rng: random.Random, cx: int, cy: int, rx: int, ry: int
) -> dict[tuple[int, int], tuple[float, float]]:
    """Blob pass: wide, organic multi-lobe crown silhouette. Returns {(x, y): (u, v)}."""
    lobes: list[tuple[int, int, int, int]] = [
        (cx, cy, int(rx * 0.72), int(ry * 0.74)),
        (cx - int(rx * 0.48), cy + int(ry * 0.12), int(rx * 0.48), int(ry * 0.52)),
        (cx + int(rx * 0.48), cy + int(ry * 0.12), int(rx * 0.48), int(ry * 0.52)),
        (cx - int(rx * 0.30), cy - int(ry * 0.36), int(rx * 0.46), int(ry * 0.46)),
        (cx + int(rx * 0.28), cy - int(ry * 0.34), int(rx * 0.44), int(ry * 0.44)),
        (cx, cy - int(ry * 0.48), int(rx * 0.42), int(ry * 0.40)),
    ]
    # Add small edge tufts for organic scalloped silhouette
    for _ in range(10):
        ang = rng.uniform(0, math.tau)
        lx = cx + int(math.cos(ang) * rx * rng.uniform(0.55, 0.78))
        ly = cy + int(math.sin(ang) * ry * rng.uniform(0.50, 0.75))
        lrx = max(4, int(rx * rng.uniform(0.16, 0.26)))
        lry = max(3, int(ry * rng.uniform(0.16, 0.26)))
        lobes.append((lx, ly, lrx, lry))

    mask: dict[tuple[int, int], tuple[float, float]] = {}
    x0, x1 = cx - rx - 4, cx + rx + 4
    y0, y1 = cy - ry - 4, cy + ry + 4
    for y in range(y0, y1 + 1):
        v = (y - (cy - ry)) / max(1, 2 * ry)
        for x in range(x0, x1 + 1):
            u = (x - cx) / max(1, rx)
            if any(((x - lx) / max(1, lrx)) ** 2 + ((y - ly) / max(1, lry)) ** 2 <= 1.0 for lx, ly, lrx, lry in lobes):
                mask[(x, y)] = (max(-1.0, min(1.0, u)), max(0.0, min(1.0, v)))

    # Despike: remove 1px spurs
    for _ in range(3):
        spurs = [p for p in mask if sum((p[0] + dx, p[1] + dy) in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) < 3]
        for p in spurs:
            del mask[p]

    # Keep only largest connected component
    best: set[tuple[int, int]] = set()
    seen: set[tuple[int, int]] = set()
    for start in mask:
        if start in seen:
            continue
        comp, stack = {start}, [start]
        while stack:
            px, py = stack.pop()
            for n in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                if n in mask and n not in comp:
                    comp.add(n)
                    stack.append(n)
        seen |= comp
        if len(comp) > len(best):
            best = comp
    return {p: mask[p] for p in best}


def _draw_fruit_cluster(local: Canvas, fx: int, fy: int, r: int, base: RGBA, hi: RGBA, sh: RGBA, leaf: RGBA) -> None:
    """Draw a 3-tone shaded fruit with top-left highlight and tiny stem/leaf."""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                if dx + dy < -r // 2:
                    col = hi
                elif dx + dy > r // 2:
                    col = sh
                else:
                    col = base
                local.set_pixel(fx + dx, fy + dy, col)
    local.set_pixel(fx, fy - r - 1, leaf)


def draw_broadleaf(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
    frame: int = 0,
) -> None:
    """Draw an oak or fruit tree natively at (w, h); default 128x128."""
    w, h = int(op.get("w", 128)), int(op.get("h", 128))
    variant = str(op.get("variant", "oak")).lower()
    sway = bool(op.get("sway", False))
    needles = _ramp(op, "needle_ramp", _NEEDLES, palette)
    bark = _ramp(op, "bark_ramp", _BARK, palette)
    rng = random.Random(int(op.get("seed", 11 if variant == "oak" else 17)))

    local = Canvas(w, h)
    cx = w // 2
    foot = h - 9
    tw = max(6, w // 9)

    if op.get("shadow", True):
        local.mark_shadow = local.mark_no_outline = True
        sc = parse_color(op.get("shadow_color", _SHADOW), palette)
        for dy in range(-3, 4):
            half = int((w // 3) * math.sqrt(max(0.0, 1 - (dy / 3.5) ** 2)))
            for dx in range(-half, half + 1):
                local.set_pixel(cx + dx + 3, foot + 2 + dy, sc)
        local.mark_shadow = local.mark_no_outline = False

    trunk_top = int(h * 0.42)
    _draw_trunk(local, rng, cx, trunk_top, foot, tw, bark)

    off = (-1, 0, 1, 0)[frame % 4] if sway else 0
    rx = int(w * 0.40)
    ry = int(h * 0.30)
    cy = max(ry + 4, int(h * 0.38))

    mask = _crown_mask(rng, cx + off, cy, rx, ry)
    # Cast shadow of crown onto trunk
    for (px, py) in mask:
        for d in (1, 2, 3, 4):
            q = (px, py + d)
            if q not in mask and 0 <= q[0] < w and 0 <= q[1] < h:
                c = local.get_pixel(*q)
                if c in bark and bark.index(c) > 0:
                    local.set_pixel(q[0], q[1], bark[0])

    tones = _shade_tier(rng, mask, cx + off, cy - ry, cy + ry, rx)
    for (px, py), tn in tones.items():
        if 0 <= px < w and 0 <= py < h:
            local.set_pixel(px, py, needles[max(0, min(len(needles) - 1, tn))])

    if variant == "fruit":
        accent = parse_color(op.get("accent_color", "roof" if "roof" in palette else "#d94e41"), palette)
        f_hi = brighten(accent, 1.32)
        f_sh = darken(accent, 0.68)
        f_r = max(1, w // 48)
        placed = 0
        attempts = 0
        while placed < 7 and attempts < 80:
            attempts += 1
            fx = cx + off + rng.randint(-int(rx * 0.68), int(rx * 0.68))
            fy = cy + rng.randint(-int(ry * 0.55), int(ry * 0.55))
            if (fx, fy) in mask and (fx - f_r, fy - f_r) in mask and (fx + f_r, fy + f_r) in mask:
                _draw_fruit_cluster(local, fx, fy, f_r, accent, f_hi, f_sh, needles[0])
                placed += 1

    canvas.blit(local, x, y)

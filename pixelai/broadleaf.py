"""Native-resolution broadleaf trees (oak, fruit): Blob -> Shape -> Shade with blade fringe."""

import random
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color
from pixelai import foliage as fo


def _draw_fruit(local: Canvas, fx: int, fy: int, r: int, base: RGBA, hi: RGBA, sh: RGBA, leaf: RGBA) -> None:
    """Shaded fruit: top-left highlight, bottom-right shade, tiny stem leaf."""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                local.set_pixel(fx + dx, fy + dy, hi if dx + dy < -r // 2 else sh if dx + dy > r // 2 else base)
    local.set_pixel(fx, fy - r - 1, leaf)


def draw_broadleaf(canvas: Canvas, x: int, y: int, palette: dict[str, RGBA], op: dict[str, Any], frame: int = 0) -> None:
    """Draw an oak or fruit tree natively at (w, h); default 128x128."""
    w, h = int(op.get("w", 128)), int(op.get("h", 128))
    variant = str(op.get("variant", "oak")).lower()
    ramp = fo.get_ramp(op, "oak", palette)
    bark = fo.get_bark(op, palette)
    rng = random.Random(int(op.get("seed", 11 if variant == "oak" else 17)))
    local = Canvas(w, h)
    cx, foot = w // 2, h - 9
    if op.get("shadow", True):
        fo.draw_ground_shadow(local, cx, foot, w, parse_color(op.get("shadow_color", fo.SHADOW), palette))
    fo.draw_trunk(local, rng, cx, int(h * 0.42), foot, max(6, w // 9), bark)

    off = (-1, 0, 1, 0)[frame % 4] if op.get("sway") else 0
    rx, ry = int(w * 0.40), int(h * 0.30)
    cy = max(ry + 6, int(h * 0.38))
    mask = fo.add_fringe(rng, fo.lobed_mask(rng, cx + off, cy, rx, ry))
    for (px, py) in mask:  # crown cast shadow on the trunk
        for d in (1, 2, 3, 4):
            q = (px, py + d)
            if q not in mask and 0 <= q[0] < w and 0 <= q[1] < h and local.get_pixel(*q) in bark[1:]:
                local.set_pixel(q[0], q[1], bark[0])
    fo.paint(local, {p: t for p, t in fo.shade_mass(rng, mask, cx + off, cy - ry, cy + ry, rx).items()
                     if 0 <= p[0] < w and 0 <= p[1] < h}, ramp)

    if variant == "fruit":
        accent = parse_color(op.get("accent_color", "#d94e41"), palette)
        r, placed = max(2, w // 40), 0
        for _ in range(80):
            if placed >= 7:
                break
            fx = cx + off + rng.randint(-int(rx * 0.68), int(rx * 0.68))
            fy = cy + rng.randint(-int(ry * 0.55), int(ry * 0.55))
            if all((fx + a, fy + b) in mask for a, b in ((0, 0), (-r, -r), (r, r), (0, -r - 1))):
                _draw_fruit(local, fx, fy, r, accent, brighten(accent, 1.32), darken(accent, 0.68), ramp.tones[1])
                placed += 1
    canvas.blit(local, x, y)

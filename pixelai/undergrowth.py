"""Native bushes and grass: leaf-dome bushes, blade tufts (varied spacing, mirrored shapes), grass patches."""

import random
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, parse_color
from pixelai import foliage as fo


def draw_bush(canvas: Canvas, x: int, y: int, palette: dict[str, RGBA], op: dict[str, Any], frame: int = 0) -> None:
    """Leaf dome with blade skirt, tufted shading and a ground shadow; default 64x52."""
    w, h = int(op.get("w", 64)), int(op.get("h", 52))
    ramp = fo.get_ramp(op, "oak", palette)
    rng = random.Random(int(op.get("seed", 5)))
    local = Canvas(w, h)
    cx, foot = w // 2, h - 8
    if op.get("shadow", True):
        fo.draw_ground_shadow(local, cx, foot, w, parse_color(op.get("shadow_color", fo.SHADOW), palette))
    rx, ry = int(w * 0.44), int(h * 0.44)
    cy = foot - int(ry * 0.45)
    off = (-1, 0, 1, 0)[frame % 4] if op.get("sway") else 0
    mask = fo.add_fringe(rng, fo.lobed_mask(rng, cx + off, cy, rx, ry, edge_lobes=10, floor=foot))
    fo.paint(local, {p: t for p, t in fo.shade_mass(rng, mask, cx + off, cy - ry, foot, rx).items()
                     if 0 <= p[0] < w and 0 <= p[1] < h}, ramp)
    canvas.blit(local, x, y)


def _blades(local: Canvas, rng: random.Random, cx: int, base_y: int, spread: int, hmin: int, hmax: int,
            dark: RGBA, light: RGBA, glint: RGBA) -> None:
    """Two-layer blade cluster: dark back row, lit front row; blades splay outward, spacing irregular."""
    for layer, (lo, hi, col) in enumerate(((hmin - 1, hmax - 2, dark), (hmin, hmax, light))):
        x = cx - spread + rng.randint(0, 2)
        while x <= cx + spread:
            lean = -1 if x < cx else 1
            height = max(2, rng.randint(max(2, lo), max(3, hi)) - (abs(x - cx) * hmax // (2 * spread + 1)))
            for k in range(height):
                px = x + lean * (k // 3)
                tip = k >= height - 2
                local.set_pixel(px, base_y - k, glint if (layer and k == height - 1) else light if (tip and layer) else col)
            if layer and height >= 5 and rng.random() < 0.5:  # leaf detail: stem with a side leaf
                local.set_pixel(x + lean * (height // 6) - lean, base_y - height // 2, dark)
            x += rng.randint(2, 5)


def draw_grass(canvas: Canvas, x: int, y: int, palette: dict[str, RGBA], op: dict[str, Any], frame: int = 0) -> None:
    """Grass tuft (default 24x16, outline-free) or `variant: patch` (default 64x40, mound with blade rim)."""
    variant = str(op.get("variant", "tuft")).lower()
    ramp = fo.get_ramp(op, "grass", palette)
    rng = random.Random(int(op.get("seed", 3)))
    if variant == "patch":
        w, h = int(op.get("w", 64)), int(op.get("h", 40))
        local = Canvas(w, h)
        cx, cy = w // 2, h // 2 + 2
        rx, ry = int(w * 0.42), int(h * 0.30)
        mask = fo.add_fringe(rng, fo.lobed_mask(rng, cx, cy, rx, ry, edge_lobes=8))
        fo.paint(local, fo.shade_mass(rng, mask, cx, cy - ry, cy + ry, rx), ramp)
    else:
        w, h = int(op.get("w", 24)), int(op.get("h", 16))
        local = Canvas(w, h)
        local.mark_no_outline = True
        sway = (-1, 0, 1, 0)[frame % 4] if op.get("sway") else 0
        _blades(local, rng, w // 2 + sway, h - 3, max(3, w // 2 - 3), max(4, h // 3), h - 5,
                ramp.tones[1], ramp.tones[3], ramp.glint)
    canvas.blit(local, x, y)

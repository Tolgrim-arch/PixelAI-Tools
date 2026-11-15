"""Native-resolution conifer (pine): Blob -> Shape -> Shade, stepped tiers, drooping bough lobes."""

import math
import random
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, parse_color
from pixelai import foliage as fo


def _tier_mask(rng: random.Random, cx: int, top: int, bottom: int, hw: int, tip: bool) -> fo.Mask:
    """Blob pass: chunky tier with drooping bough lobes. Returns {(x,y): (u,v)}."""
    height = bottom - top
    jitter, run, val = [], 0, 0
    for _ in range(height + 8):
        if run == 0:
            run, val = rng.randint(2, 4), rng.randint(-2, 3)
        jitter.append(val)
        run -= 1
    lobe_w = max(7, hw // 4)
    phases = [rng.uniform(0.35, 1.7) for _ in range(2 * hw // lobe_w + 3)]
    mask: fo.Mask = {}
    for y in range(top, bottom + 8):
        v = min((y - top) / height, 1.0)
        # Upper tier tapers from a tip; lower tiers start wide so each ledge overhangs the tier above.
        profile = v ** 0.9 if tip else 0.38 + 0.62 * v ** 1.15
        half = max(0.0, hw * profile + jitter[min(y - top, len(jitter) - 1)] * (0.5 + v))
        for x in range(cx - int(half) - 1, cx + int(half) + 2):
            if abs(x - cx) > half:
                continue
            u = (x - cx) / max(half, 1.0)
            idx = (x - cx + hw) // lobe_w
            frac = ((x - cx + hw) % lobe_w) / lobe_w
            droop = 7.0 * math.sin(math.pi * frac) ** 1.5 * phases[max(0, min(idx, len(phases) - 1))]
            if y <= bottom - 1.5 * abs(u) ** 2 + droop:
                mask[(x, y)] = (max(-1.0, min(1.0, u)), v)
    return fo.clean_mask(mask)


def draw_pine(canvas: Canvas, x: int, y: int, palette: dict[str, RGBA], op: dict[str, Any], frame: int = 0) -> None:
    """Draw a pine tree natively at (w, h); default 128x128."""
    w, h = int(op.get("w", 128)), int(op.get("h", 128))
    sway = bool(op.get("sway", False))
    ramp = fo.get_ramp(op, "pine", palette)
    bark = fo.get_bark(op, palette)
    rng = random.Random(int(op.get("seed", 7)))
    local = Canvas(w, h)
    cx, foot = w // 2, h - 9
    if op.get("shadow", True):
        fo.draw_ground_shadow(local, cx, foot, w, parse_color(op.get("shadow_color", fo.SHADOW), palette))
    canopy_top, canopy_bot = 3, foot - 17
    fo.draw_trunk(local, rng, cx, canopy_top + h // 3, foot, max(6, w // 11), bark)

    tiers = max(3, h // 25)
    max_hw = int(w * 0.43)
    for i in range(tiers - 1, -1, -1):  # bottom tier first so upper tiers overlap it
        t = i / (tiers - 1)
        bottom = int(canopy_top + (canopy_bot - canopy_top) * (0.30 + 0.70 * t))
        top = bottom - int(h * (0.20 + 0.075 * t)) if i else canopy_top
        hw = int(max_hw * (0.26 + 0.74 * t))
        off = (-1, 0, 1, 0)[frame % 4] * (i % 2 * 2 - 1) * (i > 0) if sway else 0
        mask = _tier_mask(rng, cx + off, top, bottom, hw, tip=(i == 0))
        for (px, py) in mask:  # cast shadow of this tier on whatever lies beneath it
            for d in range(1, 7):
                q = (px, py + d)
                if q not in mask and 0 <= q[0] < w and 0 <= q[1] < h:
                    c = local.get_pixel(*q)
                    if c in ramp.tones and ramp.tones.index(c) > 0:
                        local.set_pixel(q[0], q[1], ramp.tones[max(0, ramp.tones.index(c) - 2)])
        fo.paint(local, {p: t for p, t in fo.shade_mass(rng, mask, cx + off, top, bottom, hw).items()
                         if 0 <= p[0] < w and 0 <= p[1] < h}, ramp)
    canvas.blit(local, x, y)

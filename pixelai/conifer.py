"""Hand-crafted-style conifer (pine) generator built natively at the target resolution.

Follows the Blob -> Shape -> Shade method from the Wood Tutorial and the
leaf-tuft sphere shading study: no scaling of smaller sprites, every tier,
tuft and bark streak is generated at final pixel size. Light comes from the
top-left; rims facing the light brighten, rims facing away darken.
"""

import math
import random
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, parse_color

# Ramp 0 (deep pocket) .. 4 (sun highlight). Hue-shifted: shadows cool, lights warm-yellow.
_NEEDLES = ("#17382f", "#1f5236", "#2f7340", "#4c9446", "#7fb956")
_BARK = ("#2b1a1c", "#4f3224", "#744a30", "#97663d")
_SHADOW = "#1c2a2a"


def _ramp(op: dict[str, Any], key: str, default: tuple[str, ...], palette: dict[str, RGBA]) -> list[RGBA]:
    return [parse_color(c, palette) for c in op.get(key, default)]


def _tier_mask(
    rng: random.Random, cx: int, top: int, bottom: int, hw: int, tip: bool
) -> dict[tuple[int, int], tuple[float, float]]:
    """Blob pass: chunky silhouette with drooping bough lobes. Returns {(x,y): (u,v)}."""
    height = bottom - top
    mask: dict[tuple[int, int], tuple[float, float]] = {}
    # Row jitter is shared by 2-3 rows so edges form chunky clusters instead of noise.
    jitter = [0] * (height + 8)
    run, val = 0, 0
    for i in range(len(jitter)):
        if run == 0:
            run, val = rng.randint(2, 4), rng.randint(-2, 3)
        jitter[i] = val
        run -= 1
    lobe_w = max(7, hw // 4)
    phases = [rng.uniform(0.35, 1.7) for _ in range(2 * hw // lobe_w + 3)]
    for y in range(top, bottom + 6):
        v = (y - top) / height
        v_c = min(v, 1.0)
        # Upper tiers taper from a tip; lower tiers start wide so each ledge overhangs the tier above.
        profile = v_c ** 0.9 if tip else 0.38 + 0.62 * v_c ** 1.15
        half = hw * profile + jitter[y - top] * (0.5 + v_c)
        half = max(0.0, half)
        for x in range(cx - int(half) - 1, cx + int(half) + 2):
            u = (x - cx) / max(half, 1.0)
            if abs(x - cx) > half:
                continue
            # Drooping bough lobes along the underside; tips rise so boughs read as fans.
            idx = (x - cx + hw) // lobe_w
            frac = ((x - cx + hw) % lobe_w) / lobe_w
            droop = 7.0 * math.sin(math.pi * frac) ** 1.5 * phases[max(0, min(idx, len(phases) - 1))]
            floor_y = bottom - 1.5 * abs(u) ** 2 + droop
            if y > floor_y:
                continue
            mask[(x, y)] = (max(-1.0, min(1.0, u)), v)
    # Despike: drop pixels with <3 orthogonal neighbours so no hooks/stray pixels survive.
    for _ in range(3):
        spurs = [p for p in mask if sum((p[0] + dx, p[1] + dy) in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) < 3]
        for p in spurs:
            del mask[p]
    # Keep only the largest connected blob (floating specks are never valid foliage).
    best: set[tuple[int, int]] = set()
    seen: set[tuple[int, int]] = set()
    for start in mask:
        if start in seen:
            continue
        comp, stack = {start}, [start]
        while stack:
            cx0, cy0 = stack.pop()
            for n in ((cx0 + 1, cy0), (cx0 - 1, cy0), (cx0, cy0 + 1), (cx0, cy0 - 1)):
                if n in mask and n not in comp:
                    comp.add(n)
                    stack.append(n)
        seen |= comp
        if len(comp) > len(best):
            best = comp
    return {p: mask[p] for p in best}


def _tone(u: float, v: float) -> float:
    """Shape pass: broad light model, top-left lit, lower/right shaded."""
    return 2.6 - 1.5 * u - 1.9 * (v - 0.30)


def _shade_tier(
    rng: random.Random,
    mask: dict[tuple[int, int], tuple[float, float]],
    cx: int,
    top: int,
    bottom: int,
    hw: int,
) -> dict[tuple[int, int], int]:
    """Shade pass: tone ramp + clustered needle tufts + rim light/dark + shadow pockets."""
    tones: dict[tuple[int, int], int] = {}
    for (x, y), (u, v) in mask.items():
        tones[(x, y)] = int(round(_tone(u, v)))
    # Needle tufts: jittered grid; lit crescent on top-left, dark crescent on bottom-right.
    step = 6
    for gy in range(top, bottom + 5, step - 1):
        for gx in range(cx - hw, cx + hw + 1, step):
            tx = gx + rng.randint(-2, 2) + ((gy // (step - 1)) % 2) * (step // 2)
            ty = gy + rng.randint(-1, 1)
            if (tx, ty) not in mask:
                continue
            rx, ry = rng.randint(3, 4), rng.randint(2, 3)
            for dy in range(-ry, ry + 1):
                for dx in range(-rx, rx + 1):
                    p = (tx + dx, ty + dy)
                    if p not in tones or (dx / rx) ** 2 + (dy / ry) ** 2 > 1.0:
                        continue
                    lit = (dx + dy) < -rx // 2
                    dark = (dx + dy) > rx // 2 and dy >= 0
                    core = (dx + dy) < -rx
                    tones[p] += 2 if core else (1 if lit else (-1 if dark else 0))
    # Rim logic: neighbours outside the mask decide light/dark edge.
    base = dict(tones)
    for (x, y) in mask:
        if (x - 1, y - 1) not in mask or (x, y - 1) not in mask:
            base[(x, y)] = max(base[(x, y)], tones[(x, y)] + 1)
        if (x + 1, y) not in mask or (x, y + 1) not in mask:
            base[(x, y)] = min(base[(x, y)], tones[(x, y)] - 1)
    tones = base
    # Shadow pockets between boughs in the lower half + sun glints in the upper-left.
    for _ in range(max(3, hw // 5)):
        px = cx + rng.randint(-hw, hw)
        py = rng.randint(top + (bottom - top) // 2, bottom)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)) if rng.random() < 0.4 else ((0, 0), (1, 0)):
            if (px + dx, py + dy) in tones:
                tones[(px + dx, py + dy)] = 0
    for _ in range(max(2, hw // 7)):
        px = cx + rng.randint(-hw // 2, 0)
        py = rng.randint(top + 2, top + (bottom - top) // 2)
        for dx in (0, 1, 2):
            if (px + dx, py) in tones:
                tones[(px + dx, py)] = 4
    return tones


def _draw_trunk(local: Canvas, rng: random.Random, cx: int, top: int, foot: int, tw: int, bark: list[RGBA]) -> None:
    """Bark: left-lit 3-tone columns, vertical grain streaks, flared roots."""
    for y in range(top, foot + 1):
        flare = max(0, y - (foot - 12)) // 3 + (2 if y > foot - 3 else 0)
        left, right = cx - tw // 2 - flare, cx + tw // 2 + flare
        for x in range(left, right + 1):
            rel = (x - left) / max(1, right - left)
            tone = 3 if rel < 0.22 else 2 if rel < 0.5 else 1 if rel < 0.82 else 0
            local.set_pixel(x, y, bark[tone])
    for _ in range(tw * 2):
        sx = cx - tw // 2 + rng.randint(1, tw - 1)
        sy = rng.randint(top, foot - 4)
        tone = 0 if sx > cx else 1
        for dy in range(rng.randint(3, 9)):
            if sy + dy <= foot - 2:
                local.set_pixel(sx, sy + dy, bark[tone])
    for dy in range(3, 9, 3):
        local.set_pixel(cx - tw // 2 + 1, top + dy * 3, bark[3])
    # Root buttresses
    for side in (-1, 1):
        for i in range(4):
            local.set_pixel(cx + side * (tw // 2 + 3 + i), foot - (1 if i < 3 else 0), bark[0 if side > 0 else 2])


def draw_pine(canvas: Canvas, x: int, y: int, palette: dict[str, RGBA], op: dict[str, Any], frame: int = 0) -> None:
    """Draw a pine tree natively at (w, h); default 128x128."""
    w, h = int(op.get("w", 128)), int(op.get("h", 128))
    sway = bool(op.get("sway", False))
    needles = _ramp(op, "needle_ramp", _NEEDLES, palette)
    bark = _ramp(op, "bark_ramp", _BARK, palette)
    rng = random.Random(int(op.get("seed", 7)))
    local = Canvas(w, h)
    cx = w // 2
    foot = h - 9
    tw = max(6, w // 11)

    if op.get("shadow", True):
        local.mark_shadow = local.mark_no_outline = True
        sc = parse_color(op.get("shadow_color", _SHADOW), palette)
        for dy in range(-3, 4):
            half = int((w // 3) * math.sqrt(max(0.0, 1 - (dy / 3.5) ** 2)))
            for dx in range(-half, half + 1):
                local.set_pixel(cx + dx + 3, foot + 2 + dy, sc)
        local.mark_shadow = local.mark_no_outline = False

    canopy_top, canopy_bot = 3, foot - 17
    _draw_trunk(local, rng, cx, canopy_top + h // 3, foot, tw, bark)

    tiers = max(3, h // 25)
    max_hw = int(w * 0.43)
    # Bottom tier first so upper tiers overlap it.
    for i in range(tiers - 1, -1, -1):
        t = i / (tiers - 1)
        bottom = int(canopy_top + (canopy_bot - canopy_top) * (0.30 + 0.70 * t))
        th = int(h * (0.20 + 0.075 * t))
        top = bottom - th if i else canopy_top
        hw = int(max_hw * (0.26 + 0.74 * t))
        off = (-1, 0, 1, 0)[frame % 4] * (i % 2 * 2 - 1) * (i > 0) if sway else 0
        mask = _tier_mask(rng, cx + off, top, bottom, hw, tip=(i == 0))
        # Cast shadow of this tier on the tier(s) beneath (dark band, 4px lower).
        for (px, py) in mask:
            for d in (1, 2, 3, 4, 5, 6):
                q = (px, py + d)
                if q not in mask and 0 <= q[0] < w and 0 <= q[1] < h:
                    c = local.get_pixel(*q)
                    if c in needles and needles.index(c) > 0:
                        local.set_pixel(q[0], q[1], needles[max(0, needles.index(c) - 2)])
        tones = _shade_tier(rng, mask, cx + off, top, bottom, hw)
        for (px, py), tn in tones.items():
            if 0 <= px < w and 0 <= py < h:
                local.set_pixel(px, py, needles[max(0, min(len(needles) - 1, tn))])
    canvas.blit(local, x, y)

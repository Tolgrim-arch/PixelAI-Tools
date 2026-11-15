"""Shared foliage toolkit: palettes, lobed blobs, blade fringes, tuft shading and bark.

Colours were sampled from the reference studies (leaf-sphere/bush sheet, grass tutorial,
Wood tutorial). Method for every leafy mass: Blob (silhouette) -> Shape (top-left light,
lower-right shade) -> Shade (two-tone leaf tufts, rim light/dark, pockets, leaf glints with stems).
"""

import math
import random
from dataclasses import dataclass
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, parse_color

Mask = dict[tuple[int, int], tuple[float, float]]

# (pocket, t0, t1, t2, t3, t4, glint) — sampled from the references.
RAMPS: dict[str, tuple[str, ...]] = {
    "oak": ("#132420", "#17402f", "#1d5739", "#298840", "#50b640", "#8cc43c", "#b6d53c"),
    "pine": ("#132420", "#17402f", "#1d5739", "#20713b", "#298351", "#50b640", "#8cc43c"),
    "grass": ("#17402f", "#1d5739", "#3b7a3e", "#518c3c", "#84b43d", "#b6d53c", "#c2e16b"),
}
BARK = ("#361d1a", "#533828", "#81623d", "#a47d52")
SHADOW = "#1c2a2a"


@dataclass(frozen=True)
class Ramp:
    pocket: RGBA
    tones: tuple[RGBA, ...]
    glint: RGBA

    def color(self, t: int) -> RGBA:
        if t <= -1:
            return self.pocket
        if t >= len(self.tones):
            return self.glint
        return self.tones[t]


def get_ramp(op: dict[str, Any], default: str, palette: dict[str, RGBA]) -> Ramp:
    raw = [parse_color(c, palette) for c in op.get("ramp", RAMPS[default])]
    return Ramp(raw[0], tuple(raw[1:6]), raw[6])


def get_bark(op: dict[str, Any], palette: dict[str, RGBA]) -> list[RGBA]:
    return [parse_color(c, palette) for c in op.get("bark_ramp", BARK)]


def _neighbors4(p: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    return ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1))


def clean_mask(mask: Mask) -> Mask:
    """Despike 1px spurs, then keep only the largest connected blob."""
    for _ in range(3):
        for p in [p for p in mask if sum(n in mask for n in _neighbors4(p)) < 3]:
            del mask[p]
    best: set[tuple[int, int]] = set()
    seen: set[tuple[int, int]] = set()
    for start in mask:
        if start in seen:
            continue
        comp, stack = {start}, [start]
        while stack:
            for n in _neighbors4(stack.pop()):
                if n in mask and n not in comp:
                    comp.add(n)
                    stack.append(n)
        seen |= comp
        if len(comp) > len(best):
            best = comp
    return {p: mask[p] for p in best}


def lobed_mask(
    rng: random.Random, cx: int, cy: int, rx: int, ry: int, edge_lobes: int = 16, floor: int | None = None
) -> Mask:
    """Blob pass: chunky multi-lobe crown (ellipses + random edge scallops)."""
    lobes = [
        (cx, cy, rx * 0.72, ry * 0.74),
        (cx - rx * 0.48, cy + ry * 0.12, rx * 0.48, ry * 0.52),
        (cx + rx * 0.48, cy + ry * 0.12, rx * 0.48, ry * 0.52),
        (cx - rx * 0.30, cy - ry * 0.36, rx * 0.46, ry * 0.46),
        (cx + rx * 0.28, cy - ry * 0.34, rx * 0.44, ry * 0.44),
        (cx, cy - ry * 0.48, rx * 0.42, ry * 0.40),
    ]
    for _ in range(edge_lobes):
        ang = rng.uniform(0, math.tau)
        lobes.append((
            cx + math.cos(ang) * rx * rng.uniform(0.55, 0.80),
            cy + math.sin(ang) * ry * rng.uniform(0.50, 0.78),
            max(4.0, rx * rng.uniform(0.15, 0.27)),
            max(3.0, ry * rng.uniform(0.15, 0.27)),
        ))
    mask: Mask = {}
    for y in range(cy - ry - 4, (floor if floor is not None else cy + ry + 4) + 1):
        v = max(0.0, min(1.0, (y - (cy - ry)) / max(1, 2 * ry)))
        for x in range(cx - rx - 4, cx + rx + 5):
            if any(((x - lx) / a) ** 2 + ((y - ly) / b) ** 2 <= 1.0 for lx, ly, a, b in lobes):
                mask[(x, y)] = (max(-1.0, min(1.0, (x - cx) / max(1, rx))), v)
    return clean_mask(mask)


def add_fringe(rng: random.Random, mask: Mask) -> Mask:
    """Blade fringe: splayed (mirrored) blades under the mass, short lit sprouts on top, irregular spacing."""
    xs = [x for x, _ in mask]
    cx = (min(xs) + max(xs)) // 2
    low: dict[int, int] = {}
    high: dict[int, int] = {}
    for x, y in mask:
        low[x] = max(low.get(x, y), y)
        high[x] = min(high.get(x, y), y)
    out = dict(mask)
    x = min(xs) + rng.randint(0, 2)
    while x <= max(xs):
        if x in low:
            lean = -1 if x < cx else 1
            for k in range(1, rng.randint(2, 4) + 1):
                out.setdefault((x + lean * ((k - 1) // 2), low[x] + k), (mask[(x, low[x])][0], 1.0))
        x += rng.randint(2, 5)
    x = min(xs) + rng.randint(1, 4)
    while x <= max(xs):
        if x in high and rng.random() < 0.7:
            lean = -1 if x < cx else 1
            for k in range(1, rng.randint(1, 2) + 1):
                out.setdefault((x + lean * (k // 2), high[x] - k), (mask[(x, high[x])][0], 0.0))
        x += rng.randint(3, 6)
    return out


def shade_mass(rng: random.Random, mask: Mask, cx: int, top: int, bottom: int, hw: int) -> dict[tuple[int, int], int]:
    """Shape + Shade passes. Tone -1 = pocket, 0..4 = ramp, >=5 = glint."""
    tones = {p: int(round(2.6 - 1.5 * u - 1.9 * (v - 0.30))) for p, (u, v) in mask.items()}
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
                    if dx + dy < -rx:
                        tones[p] += 2
                    elif dx + dy < -rx // 2:
                        tones[p] += 1
                    elif dx + dy > rx // 2 and dy >= 0:
                        tones[p] -= 1
    shaded = dict(tones)
    for p in mask:
        x, y = p
        if (x - 1, y - 1) not in mask or (x, y - 1) not in mask:
            shaded[p] = max(shaded[p], tones[p] + 1)
        if (x + 1, y) not in mask or (x, y + 1) not in mask:
            shaded[p] = min(shaded[p], tones[p] - 1)
    for _ in range(max(3, hw // 5)):
        px = cx + rng.randint(-hw, hw)
        py = rng.randint(top + (bottom - top) // 2, bottom)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)) if rng.random() < 0.4 else ((0, 0), (1, 0)):
            if (px + dx, py + dy) in shaded:
                shaded[(px + dx, py + dy)] = -1
    # Leaf glints: 3px lit leaf with a darker stem pixel beneath its root.
    for _ in range(max(3, hw // 6)):
        px = cx + rng.randint(-hw // 2, 0)
        py = rng.randint(top + 2, top + (bottom - top) // 2)
        for dx in (0, 1, 2):
            if (px + dx, py) in shaded:
                shaded[(px + dx, py)] = 5
        if (px, py + 1) in shaded:
            shaded[(px, py + 1)] = max(0, shaded[(px, py + 1)] - 2)
    return shaded


def paint(local: Canvas, tones: dict[tuple[int, int], int], ramp: Ramp) -> None:
    for (x, y), t in tones.items():
        local.set_pixel(x, y, ramp.color(t))


def draw_ground_shadow(local: Canvas, cx: int, foot: int, w: int, color: RGBA) -> None:
    local.mark_shadow = local.mark_no_outline = True
    for dy in range(-3, 4):
        half = int((w // 3) * math.sqrt(max(0.0, 1 - (dy / 3.5) ** 2)))
        for dx in range(-half, half + 1):
            local.set_pixel(cx + dx + 3, foot + 2 + dy, color)
    local.mark_shadow = local.mark_no_outline = False


def draw_trunk(local: Canvas, rng: random.Random, cx: int, top: int, foot: int, tw: int, bark: list[RGBA]) -> None:
    """Bark: left-lit 4-tone columns, vertical grain streaks, flared roots."""
    for y in range(top, foot + 1):
        flare = max(0, y - (foot - 12)) // 3 + (2 if y > foot - 3 else 0)
        left, right = cx - tw // 2 - flare, cx + tw // 2 + flare
        for x in range(left, right + 1):
            rel = (x - left) / max(1, right - left)
            local.set_pixel(x, y, bark[3 if rel < 0.22 else 2 if rel < 0.5 else 1 if rel < 0.82 else 0])
    for _ in range(tw * 2):
        sx = cx - tw // 2 + rng.randint(1, tw - 1)
        sy = rng.randint(top, foot - 4)
        for dy in range(rng.randint(3, 9)):
            if sy + dy <= foot - 2:
                local.set_pixel(sx, sy + dy, bark[0 if sx > cx else 1])
    for side in (-1, 1):
        for i in range(4):
            local.set_pixel(cx + side * (tw // 2 + 3 + i), foot - (1 if i < 3 else 0), bark[0 if side > 0 else 2])

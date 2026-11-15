"""Leaf-stamp foliage studies recreated from the reference sheet.

Technique (from the reference): flat band geometry (light / base / shade / deep) first, then tiny
leaf stamps are interleaved across band boundaries (light leaves poke into shade, dark leaves into light),
the reach grows per stage, and the rim finally frays into dark blades. Shapes: sphere, grass mound,
clump bush, seamless leaf tiles (incl. cross seam-check and vertical fade).
"""

import math
import random
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, parse_color
from pixelai import foliage as fo

# Sampled from the reference sheet: light, base, shade, deep.
BAND = ("#54bb34", "#2a8357", "#22554c", "#214337")
BUSH = ("#0a1410", "#142320", "#1d5a52", "#2a8357", "#54bb34")
GROUND = "#596976"

_LEAVES = (
    ((1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (0, 3)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (1, 3)),
    ((0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2), (1, 3)),
)

# (light ellipse, base disc, deep disc, reach, fringe) per stage; offsets/radii are fractions of r.
_L1 = (-0.18, -0.40, 0.73, 0.56)
_L2 = (-0.39, -0.48, 0.57, 0.57)
_SPHERE = {
    "A": [(None, None, None, 0, 0.0), (_L1, None, None, 0, 0.0), (_L1, None, None, 3, 0.0),
          (_L1, (-0.15, -0.15, 0.95), None, 6, 0.0), (_L1, (-0.15, -0.15, 0.88), (-0.2, -0.2, 1.02), 9, 0.5)],
    "B": [(_L2, (-0.17, -0.2, 0.88), None, 0, 0.0), (_L2, (-0.17, -0.2, 0.88), None, 3, 0.0),
          (_L2, (-0.17, -0.2, 0.88), None, 5, 0.0), (_L2, (-0.17, -0.2, 0.88), (-0.2, -0.2, 1.0), 7, 0.4),
          (_L2, (-0.17, -0.2, 0.88), (-0.2, -0.2, 1.0), 9, 0.8)],
}
_MOUND = [(0, 0.0), (4, 0.3), (7, 0.5), (10, 0.7), (12, 0.9)]
_BUSH_STAGE = [(2.0, 0.4), (2.2, 1.0), (2.4, 1.5), (2.5, 1.7), (2.6, 1.3)]
_FADE = ((0.0, "#288743", "#54bb34"), (0.35, "#22654a", "#2a8357"), (0.55, "#2d4e43", "#22554c"), (0.8, "#223d36", "#2d4e43"))
_TILES = {
    "a": (32, "#288743", ("#54bb34", "#54bb34", "#2c7c5f")),
    "b": (32, "#155e33", ("#2a8357", "#54bb34", "#1d5a52")),
    "d": (64, "#288743", ("#54bb34", "#54bb34", "#155e33")),
    "fade": (64, "#288743", ("#54bb34",)),
}


def _ring(d: int) -> list[tuple[int, int]]:
    return [(dx, dy) for dx in range(-d, d + 1) for dy in range(-d, d + 1) if max(abs(dx), abs(dy)) == d]


def _leaf(rng: random.Random, lean: int, long: bool) -> list[tuple[int, int]]:
    """Leaf stamp (drooping); `long` gives a grass blade. Mirrored by `lean` so similar shapes mirror."""
    if long:
        n = rng.randint(4, 7)
        cells = [(0, k) for k in range(n)] + [(1, n - 2), (1, n - 1)]
    else:
        cells = list(rng.choice(_LEAVES))
    if lean > 0:
        w = max(dx for dx, _ in cells) + 1
        cells = [(w - 1 - dx, dy) for dx, dy in cells]
    return cells


def _stamp(rng: random.Random, band: dict[tuple[int, int], int], cx: int, cy: int, reach: int,
           fringe: float, long_from: int | None, step: tuple[int, int] = (4, 4)) -> dict[tuple[int, int], int]:
    """Interleave leaf stamps across band boundaries, then fray the lower-right rim into dark blades."""
    out = dict(band)
    if reach > 0:
        xs, ys = [p[0] for p in band], [p[1] for p in band]
        rings = {d: _ring(d) for d in range(1, reach + 1)}
        for j, y0 in enumerate(range(min(ys), max(ys) + 1, step[1])):
            for x0 in range(min(xs), max(xs) + 1, step[0]):
                ax, ay = x0 + (j % 2) * (step[0] // 2) + rng.randint(-1, 1), y0 + rng.randint(-1, 1)
                b = band.get((ax, ay))
                if b is None:
                    continue
                hit = next(((d, band[(ax + dx, ay + dy)]) for d in rings for dx, dy in rings[d]
                            if band.get((ax + dx, ay + dy), b) != b), None)
                if hit is None or rng.random() > 0.95 - 0.6 * (hit[0] - 1) / reach:
                    continue
                lean = -1 if ax < cx else 1
                for dx, dy in _leaf(rng, lean, long_from is not None and ay > long_from):
                    if (ax + dx, ay + dy) in out:
                        out[(ax + dx, ay + dy)] = hit[1]
    if fringe > 0:
        for (x, y), b in sorted(band.items()):
            if (x - cx) + (y - cy) <= 0:
                continue
            lean = -1 if x < cx else 1
            if (x, y + 1) not in band and rng.random() < fringe:
                for k in range(1, rng.randint(1, 3) + 1):
                    out.setdefault((x + lean * ((k - 1) // 2), y + k), min(b + 1, 3))
            if (x + 1, y) not in band and x > cx and rng.random() < fringe * 0.6:
                for k in range(1, rng.randint(1, 2) + 1):
                    out.setdefault((x + k, y + k // 2), min(b + 1, 3))
    return out


def _disc_bands(cx: int, cy: int, r: int, light, base, deep) -> dict[tuple[int, int], int]:
    out: dict[tuple[int, int], int] = {}
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy > (r + 0.5) ** 2:
                continue
            b = 1
            if base and (dx - base[0] * r) ** 2 + (dy - base[1] * r) ** 2 > (base[2] * r) ** 2:
                b = 2
            if deep and (dx - deep[0] * r) ** 2 + (dy - deep[1] * r) ** 2 > (deep[2] * r) ** 2:
                b = 3
            if light and ((dx - light[0] * r) / (light[2] * r)) ** 2 + ((dy - light[1] * r) / (light[3] * r)) ** 2 <= 1:
                b = 0
            out[(x, y)] = b
    return out


def _mound_bands(cx: int, hw: int, stage: int) -> tuple[dict[tuple[int, int], int], int]:
    ry, top_cy = 15, 17
    tip = top_cy + ry + 15
    out: dict[tuple[int, int], int] = {}
    for y in range(top_cy - ry, tip + 1):
        t = (y - top_cy) / (tip - top_cy)
        for x in range(cx - hw - 1, cx + hw + 2):
            dx = x - cx
            if (dx / hw) ** 2 + ((y - top_cy) / ry) ** 2 > 1.0 and not (t >= 0 and abs(dx) <= hw * (1 - t) ** 0.5):
                continue
            if (dx / (hw * 0.84)) ** 2 + ((y - top_cy + 1) / (ry * 0.72)) ** 2 <= 1:
                out[(x, y)] = 0
            elif y <= top_cy + ry * 0.45:
                out[(x, y)] = 1
            else:
                out[(x, y)] = 2 if (t < 0.6 or stage < 3) else 3
    return out, top_cy


def _paint(local: Canvas, bands: dict[tuple[int, int], int], colors: list[RGBA]) -> None:
    for (x, y), b in bands.items():
        local.set_pixel(x, y, colors[b])


def _clump(rng: random.Random) -> set[tuple[int, int]]:
    """Leaf clump: two upper lobes + one wider lower lobe (soft notch on top)."""
    s = rng.uniform(0.75, 0.95)
    lobes = ((-1.6, -0.8, 2.5 * s, 2.0 * s), (1.6, -0.8, 2.5 * s, 2.0 * s), (0.0, 0.9, 3.4 * s, 2.2 * s))
    return {(x, y) for x in range(-7, 8) for y in range(-5, 6)
            if any(((x - lx) / a) ** 2 + ((y - ly) / b) ** 2 <= 1 for lx, ly, a, b in lobes)}


def _draw_bush(local: Canvas, rng: random.Random, palette: dict[str, RGBA], op: dict[str, Any], w: int, h: int, stage: int) -> None:
    ramp = [parse_color(c, palette) for c in op.get("bush_ramp", BUSH)]
    cx, cy = w // 2, h // 2 - 2
    rx = ry = int(w * 0.40)
    if op.get("shadow", True):
        local.mark_shadow = local.mark_no_outline = True
        sc = parse_color(op.get("shadow_color", GROUND), palette)
        for dy in range(-6, 7):
            half = int((rx + 1) * math.sqrt(max(0.0, 1 - (dy / 6.5) ** 2)))
            for dx in range(-half, half + 1):
                local.set_pixel(cx + dx - 2, cy + ry + 4 + dy, sc)
        local.mark_shadow = local.mark_no_outline = False
    mask = fo.lobed_mask(rng, cx, cy, rx, rx, edge_lobes=14)
    for x, y in mask:
        local.set_pixel(x, y, ramp[0])
    base_l, gain = _BUSH_STAGE[stage]
    spots = [(cx + dx, cy + dy) for dx in range(-rx, rx + 1, 5) for dy in range(-rx, rx + 1, 4)]
    rng.shuffle(spots)
    spots.sort(key=lambda p: p[1] + rng.randint(-3, 3))  # back-to-front, jittered
    for sx0, sy0 in spots:
        ax, ay = sx0 + rng.randint(-2, 2), sy0 + rng.randint(-1, 1)
        if (ax, ay) not in mask:
            continue
        u, v = mask[(ax, ay)]
        lvl = max(1, min(4, round(base_l + gain * (-0.65 * u - 1.1 * (v - 0.45)) + rng.uniform(-0.4, 0.4))))
        cells = _clump(rng)
        for dx, dy in cells:
            col = ramp[lvl]
            if (dx, dy + 1) not in cells:
                col = ramp[max(1, lvl - 1)]
            elif (dx - 1, dy - 1) not in cells and lvl < 4:
                col = ramp[lvl + 1]
            local.set_pixel(ax + dx, ay + dy, col)


def _draw_tile(rng: random.Random, palette: dict[str, RGBA], variant: str) -> Canvas:
    n, base, stamps = _TILES[variant]
    cells = {(x, y): parse_color(base, palette) for x in range(n) for y in range(n)}
    sx, sy = 4, 5
    for j, y0 in enumerate(range(0, n, sy)):
        for x0 in range(0, n, sx):
            ax, ay = x0 + (j % 2) * (sx // 2) + rng.randint(-1, 1), y0 + rng.randint(-1, 1)
            col = rng.choice(stamps)
            if variant == "fade":
                col = [s for s in _FADE if s[0] <= max(0, ay) / n][-1][2]
            for dx, dy in _leaf(rng, rng.choice((-1, 1)), False):
                cells[((ax + dx) % n, (ay + dy) % n)] = parse_color(col, palette)
    if variant == "fade":
        noise = {(i, j): rng.randint(-7, 7) for i in range(n // 3 + 1) for j in range(n // 2 + 1)}
        for (x, y) in list(cells):
            seg = [s for s in _FADE if s[0] <= min(1.0, max(0.0, (y + noise[(x // 3, y // 2)]) / n))][-1]
            if cells[(x, y)] == parse_color("#288743", palette):
                cells[(x, y)] = parse_color(seg[1], palette)
            if y < 5:
                cells[(x, y)] = parse_color("#52ba3d", palette)
    tile = Canvas(n, n)
    tile.mark_no_outline = True
    for (x, y), c in cells.items():
        tile.set_pixel(x, y, c)
    return tile


def draw_leafstudy(canvas: Canvas, x: int, y: int, palette: dict[str, RGBA], op: dict[str, Any], frame: int = 0) -> None:
    """`shape`: sphere (style A|B, stage 0-4) | mound | bush | tile (variant a|b|d|fade, layout cross)."""
    shape = str(op.get("shape", "sphere")).lower()
    stage = max(0, min(4, int(op.get("stage", 4))))
    rng = random.Random(int(op.get("seed", 9)))
    colors = [parse_color(c, palette) for c in op.get("band_colors", BAND)]
    if shape == "tile":
        tile = _draw_tile(rng, palette, str(op.get("variant", "a")))
        if op.get("layout") == "cross":
            n = tile.width
            full = Canvas(n * 2, n * 2)
            full.mark_no_outline = True
            for yy in range(n * 2):
                for xx in range(n * 2):
                    if n // 2 <= xx < n * 3 // 2 or n // 2 <= yy < n * 3 // 2:
                        full.set_pixel(xx, yy, tile.get_pixel((xx - n // 2) % n, (yy - n // 2) % n))
            tile = full
        canvas.blit(tile, x, y)
        return
    w, h = int(op.get("w", 64 if shape != "sphere" else 62)), int(op.get("h", 60 if shape == "bush" else 52 if shape == "mound" else 62))
    local = Canvas(w, h)
    cx = w // 2
    if shape == "bush":
        _draw_bush(local, rng, palette, op, w, h, stage)
    elif shape == "mound":
        bands, top_cy = _mound_bands(cx, w // 2 - 2, stage)
        reach, fr = _MOUND[stage]
        _paint(local, _stamp(rng, bands, cx, top_cy, reach, fr, top_cy, step=(3, 3)), colors)
    else:
        r = int(op.get("r", 29))
        light, base, deep, reach, fr = _SPHERE[str(op.get("style", "A")).upper()][stage]
        bands = _disc_bands(cx, h // 2, r, light, base, deep)
        _paint(local, _stamp(rng, bands, cx, h // 2, reach, fr, None), colors)
    canvas.blit(local, x, y)

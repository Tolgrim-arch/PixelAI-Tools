"""Native-resolution broadleaf trees (oak, fruit) using the band + leaf-stamp method from leafstudy rows 2-3."""

import random
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color
from pixelai import foliage as fo
from pixelai import leafstudy as ls


SAKURA_BANDS = ("#ffe1ed", "#f6a9c7", "#dc6c9f", "#923f76")


def _draw_fruit(local: Canvas, fx: int, fy: int, r: int, base: RGBA, hi: RGBA, sh: RGBA, leaf: RGBA) -> None:
    """Shaded fruit: top-left highlight, bottom-right shade, tiny stem leaf."""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                local.set_pixel(fx + dx, fy + dy, hi if dx + dy < -r // 2 else sh if dx + dy > r // 2 else base)
    # Apple cleft, short stem and offset leaf keep fruit legible beyond a red dot.
    local.set_pixel(fx, fy - r, sh)
    local.set_pixel(fx, fy - r - 1, (112, 75, 44, 255))
    local.set_pixel(fx + 1, fy - r - 1, leaf)
    if r >= 3:
        local.set_pixel(fx + 2, fy - r - 2, brighten(leaf, 1.3))
        local.set_pixel(fx - 1, fy - 1, (255, 225, 175, 255))


def _draw_orchard_fruit(
    local: Canvas, fx: int, fy: int, r: int, base: RGBA, leaf: RGBA, kind: str,
) -> None:
    highlight, shade = brighten(base, 1.28), darken(base, .66)
    if kind == "apple" and r == 2:
        _draw_fruit(local, fx, fy, r, base, highlight, shade, leaf)
        return
    if kind == "pear":
        points = [(0, -r - 1), (1, -r), (1, -1), (r, 1), (r, r - 1),
                  (r - 1, r), (1 - r, r), (-r, r - 1), (-r, 1), (-1, -1), (-1, -r)]
        patch = [(0, -r), (0, -1), (1, 1), (0, r - 1), (1 - r, r - 1), (-r, 1), (-1, 0)]
    else:
        points = [(-r, -1), (1 - r, 1 - r), (-1, -r), (0, 1 - r),
                  (1, -r), (r, -1), (r, 1), (r - 1, r),
                  (0, r - 1), (1 - r, r), (-r, 1)]
        patch = [(-r, -1), (1 - r, 1 - r), (-1, -r), (1, -1), (0, 1), (1 - r, 1)]
    local.draw_polygon([(fx + x, fy + y) for x, y in points], shade, filled=True)
    local.draw_polygon([(fx + x, fy + y) for x, y in patch], base, filled=True)
    local.draw_line(fx - 1, fy - 1, fx - 1, fy + (kind == "pear"), highlight)
    stem_y = fy - r - (2 if kind == "pear" else 1)
    local.set_pixel(fx, stem_y, (112, 75, 44, 255))
    local.draw_line(fx + 1, stem_y, fx + 2, stem_y - 1, brighten(leaf, 1.4))


def _draw_sakura(
    local: Canvas, palette: dict[str, RGBA], op: dict[str, Any], frame: int,
    blossom: list[RGBA],
) -> None:
    """Draw an open, branch-led cherry tree rather than a solid recolored broadleaf crown."""
    w, h = local.width, local.height
    rng = random.Random(int(op.get("seed", 29)))
    cx, foot = w // 2, h - max(7, h // 14)
    sway = (-1, 0, 1, 0)[frame % 4] if op.get("sway") else 0
    bark = [parse_color(c, palette) for c in op.get("bark_ramp", fo.BARK)]
    shadow = parse_color(op.get("shadow_color", fo.SHADOW), palette)

    if op.get("shadow", True):
        fo.draw_ground_shadow(local, cx, foot, w, shadow)

    # Low, split trunk with visible boughs: the key cherry-tree silhouette cue.
    trunk_top = int(h * 0.48)
    fo.draw_trunk(local, rng, cx, trunk_top, foot, max(4, w // 10), bark)
    branch_col = bark[2]
    for pts in (
        ((cx, trunk_top + 12), (cx - 10 + sway, trunk_top - 2), (cx - 18 + sway, trunk_top - 8)),
        ((cx, trunk_top + 8), (cx + 9 + sway, trunk_top - 5), (cx + 19 + sway, trunk_top - 10)),
        ((cx - 4, trunk_top + 4), (cx - 3 + sway, trunk_top - 10), (cx - 8 + sway, trunk_top - 17)),
    ):
        local.draw_line(*pts[0], *pts[1], branch_col)
        local.draw_line(*pts[1], *pts[2], branch_col)

    # Five airy blossom masses with gaps between them; each gets petal highlights.
    clusters = (
        (cx - 18 + sway, int(h * .29), 7, 5),
        (cx - 7 + sway, int(h * .20), 8, 5),
        (cx + 7 + sway, int(h * .23), 8, 6),
        (cx + 18 + sway, int(h * .34), 7, 5),
        (cx - 1 + sway, int(h * .36), 9, 5),
    )
    for i, (px, py, rx, ry) in enumerate(clusters):
        local.draw_ellipse(px, py + 1, rx, ry, blossom[2], filled=True)
        local.draw_ellipse(px, py, max(2, rx - 1), max(2, ry - 1), blossom[1], filled=True)
        for j in range(4):
            bx = px + rng.randint(-rx + 2, rx - 2)
            by = py + rng.randint(-ry + 1, ry - 1)
            if ((bx - px) / max(1, rx)) ** 2 + ((by - py) / max(1, ry)) ** 2 <= 1:
                local.set_pixel(bx, by, blossom[0])
        local.set_pixel(px + (i % 3) - 1, py, blossom[0])
        # Dark pink one-pixel calyxes make the masses read as blossoms, not foliage.
        local.set_pixel(px, py + min(ry, 2), blossom[2])

    local.mark_no_outline = True
    for i in range(max(3, w // 18)):
        phase = (frame + i * 2) % 8
        px = cx - w // 3 + ((i * 13 + phase * 3) % max(1, w // 2))
        py = int(h * .42) + ((i * 7 + phase * 4) % max(5, foot - int(h * .42)))
        local.set_pixel(px, py, blossom[i % 2])
    local.mark_no_outline = False


def _crown_bands(cx: int, cy: int, rx: int, ry: int, rng: random.Random) -> dict[tuple[int, int], int]:
    """Build multi-lobe crown with flat 4-band shading (0=light, 1=base, 2=shade, 3=deep) like leafstudy rows 2-3."""
    # Offset branch crowns leave deep sky notches between the lower boughs.
    handed = rng.choice((-1, 1))
    lobes = (
        (cx - int(rx * .45), cy + int(ry * .22), int(rx * .40)),
        (cx + int(rx * .48), cy + int(ry * .38), int(rx * .36)),
        (cx + handed * int(rx * .15), cy - int(ry * .53), int(rx * .43)),
        (cx - int(rx * .48), cy - int(ry * .30), int(rx * .36)),
        (cx + int(rx * .46), cy - int(ry * .08), int(rx * .39)),
        (cx - handed * int(rx * .14), cy + int(ry * .04), int(rx * .42)),
    )
    bands: dict[tuple[int, int], int] = {}
    # Paint back-to-front / bottom-to-top so upper-left lobes overlap cleanly
    for lx, ly, lr in lobes:
        lx += rng.randint(-max(1, rx // 9), max(1, rx // 9))
        ly += rng.randint(-max(1, ry // 8), max(1, ry // 8))
        lr = max(2, lr + rng.randint(-max(1, rx // 12), max(1, rx // 12)))
        disc = ls._disc_bands(lx, ly, lr, ls._L2, (-0.17, -0.2, 0.88), (-0.2, -0.2, 1.0))
        for p, b in disc.items():
            # Keep brighter band if already covered by an upper lobe, or overwrite from upper lobes
            if p not in bands or b < bands[p]:
                bands[p] = b
    return bands


def draw_broadleaf(canvas: Canvas, x: int, y: int, palette: dict[str, RGBA], op: dict[str, Any], frame: int = 0) -> None:
    """Draw an oak or fruit tree natively at (w, h); defaults to canvas size."""
    w, h = int(op.get("w", canvas.width)), int(op.get("h", canvas.height))
    variant = str(op.get("variant", "oak")).lower()
    raw_bands = op.get("band_colors")
    if raw_bands is None and isinstance(op.get("ramp"), (list, tuple)) and len(op["ramp"]) >= 4:
        r = op["ramp"]
        raw_bands = [r[-2], r[-3], r[1], r[0]] if len(r) >= 6 else [r[3], r[2], r[1], r[0]]
    default_bands = SAKURA_BANDS if variant == "sakura" else ls.BAND
    if not raw_bands and "color" in op:
        base = parse_color(op["color"], palette)
        colors = [brighten(base, 1.3), base, darken(base, .72), darken(base, .47)]
    else:
        colors = [parse_color(c, palette) for c in (raw_bands or default_bands)]
    bark = fo.get_bark(op, palette)
    seed = int(op.get("seed", 11 if variant == "oak" else 17))
    rng = random.Random(seed)
    local = Canvas(w, h)
    if variant == "sakura":
        _draw_sakura(local, palette, op, frame, colors)
        canvas.blit(local, x, y)
        return
    # Reserve enough bottom margin for the 7px-tall ground shadow and its outline.
    cx, foot = w // 2, h - max(7, h // 14)
    if op.get("shadow", True):
        fo.draw_ground_shadow(local, cx, foot, w, parse_color(op.get("shadow_color", fo.SHADOW), palette))

    off = (-1, 0, 1, 0)[frame % 4] if op.get("sway") else 0
    rx, ry = int(w * 0.36), int(h * 0.28)
    cy = max(ry + 4, int(h * 0.38))
    fo.draw_broadleaf_trunk(local, random.Random(seed ^ 0xACE), cx, cy, rx, ry, foot, bark)
    bands = _crown_bands(cx + off, cy, rx, ry, rng)
    stamped = ls._stamp(rng, bands, cx + off, cy, reach=max(4, round(9 * w / 128)), fringe=0.30, long_from=None, step=(7, 6))
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
        fruit = str(op.get("fruit", "apple")).lower()
        if fruit not in {"apple", "pear"}:
            raise ValueError(f"Unknown tree fruit: {fruit!r}; choose apple or pear")
        r = max(2, w // 20)
        limit = 5 if w < 96 else 7
        positions: list[tuple[int, int]] = []
        local.clip_to_opaque = True
        for _ in range(120):
            if len(positions) >= limit:
                break
            fx = cx + off + rng.randint(-int(rx * 0.65), int(rx * 0.65))
            fy = cy + rng.randint(-int(ry * 0.55), int(ry * 0.55))
            if any((fx - px) ** 2 + (fy - py) ** 2 < (2 * r + 3) ** 2 for px, py in positions):
                continue
            if all((fx + a, fy + b) in stamped for a, b in
                   ((-r, 1), (r, 1), (-r + 1, r), (r - 1, r), (0, -r), (2, -r - 3))):
                _draw_orchard_fruit(local, fx, fy, r, accent, colors[2], fruit)
                positions.append((fx, fy))
        local.clip_to_opaque = False
    elif variant == "sakura":
        # Bright blossom flecks break up the pink crown without dark internal linework.
        for _ in range(max(8, w // 5)):
            px = cx + off + rng.randint(-int(rx * 0.72), int(rx * 0.72))
            py = cy + rng.randint(-int(ry * 0.62), int(ry * 0.58))
            if (px, py) in stamped:
                local.set_pixel(px, py, colors[0])
                if (px + 1, py) in stamped and rng.random() < 0.55:
                    local.set_pixel(px + 1, py, colors[1])

        # A few falling petals make every wind frame distinct. They intentionally
        # remain outline-free so the external silhouette rule is not applied to dust-sized details.
        local.mark_no_outline = True
        for i in range(max(3, w // 18)):
            phase = (frame + i * 2) % 8
            px = cx - rx + ((i * 13 + phase * 3) % max(1, rx * 2))
            py = cy + ry // 3 + ((i * 7 + phase * 4) % max(5, foot - (cy + ry // 3)))
            local.set_pixel(px, py, colors[0 if i % 3 == 0 else 1])
        local.mark_no_outline = False
    canvas.blit(local, x, y)

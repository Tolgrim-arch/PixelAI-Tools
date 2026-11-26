"""Parametric cozy foliage, trees, faceted rocks, flowers, and detailed 4-stage crops."""

import random
from typing import Any
from pixelai import broadleaf, conifer, leafstudy, undergrowth
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, ground_shadow_color, parse_color


def _draw_ground_patch(
    local: Canvas, cx: int, cy: int, rx: int, ry: int, kind: str, palette: dict[str, RGBA]
) -> None:
    if kind == "none":
        return
    base = parse_color("soil" if kind == "soil" else "grass", palette) if (kind in palette or "grass" in palette) else (92, 168, 76, 255)
    local.mark_no_outline = True
    local.draw_ellipse(cx, cy, rx, ry, darken(base, 0.78), filled=True)
    local.draw_ellipse(cx, cy - 1, max(2, rx - 1), max(1, ry), base, filled=True)
    if kind == "soil":
        clod_l = brighten(base, 1.15)
        for ox in range(-rx + 2, rx - 1, 3):
            local.set_pixel(cx + ox, cy - 1, clod_l)
    local.mark_no_outline = False


def _draw_rock(
    canvas: Canvas, variant: str, seed: int,
    stone: RGBA, moss: RGBA, ore: RGBA,
) -> None:
    rng = random.Random(seed)
    cx, foot = canvas.width // 2, canvas.height - 4
    radius = max(4, canvas.width // (4 if variant == "mossy" else 5))
    height = radius if variant == "mossy" else round(radius * 1.35)
    rise = min(height + rng.randint(0, max(2, radius // 3)), max(3, foot - 2))
    drift = max(1, radius // 4)
    left = (cx - radius - 2, foot - 1)
    shoulder = (cx - radius + rng.randint(0, drift), foot - rise + max(2, rise // 3))
    crest = (cx - radius // 2 + rng.randint(-drift, drift), foot - rise)
    ridge = (cx + radius // 3 + rng.randint(0, drift), crest[1] + rng.randint(1, max(2, rise // 3)))
    right = (cx + radius + rng.randint(-drift, drift), foot - max(2, rise // 3))
    heel = (right[0] - 1, foot - 1)
    base = (cx + radius // 4, foot)
    join = (cx + rng.randint(-drift, drift), foot - max(1, rise // 3))
    side = darken(stone, .72)

    canvas.draw_polygon([left, shoulder, crest, ridge, right, heel, base], side, filled=True)
    canvas.draw_polygon([left, shoulder, crest, ridge, join], stone, filled=True)
    canvas.draw_polygon([shoulder, crest, ridge, join], brighten(stone, 1.22), filled=True)
    canvas.draw_polygon([left, join, base], darken(stone, .86), filled=True)

    # Each material follows a facet. Clip small clusters to existing rock pixels.
    canvas.clip_to_opaque = True
    try:
        # Crisp chiseled ridge highlight and lower facet crevice for rock readability
        canvas.draw_line(shoulder[0], shoulder[1], crest[0], crest[1], brighten(stone, 1.32))
        canvas.draw_line(left[0] + 2, join[1], join[0], join[1], darken(stone, 0.64))
        if variant == "mossy":
            x, y = crest
            tip_x = (ridge[0] + join[0]) // 2
            spread = max(2, (ridge[0] - x) // 3)
            canvas.draw_polygon(
                [(x, y), ridge, (tip_x + 1, ridge[1] + 2),
                 (tip_x - 2, ridge[1] + 3), (x + spread, y + 4),
                 (x + 1, y + 6), (x - 2, y + 3)],
                darken(moss, .76), filled=True,
            )
            canvas.draw_polygon(
                [(x, y), ridge, (tip_x - 1, ridge[1] + 1),
                 (x + spread, y + 2), (x + 1, y + 4), (x - 2, y + 2)],
                moss, filled=True,
            )
            canvas.draw_line(x, y + 1, x + spread - 1, y + 1, brighten(moss, 1.22))
            canvas.draw_line(x - 2, y + 4, x - 1, y + 4, moss)
            canvas.set_pixel(x + spread - 1, y + 5, darken(moss, .86))
        elif variant == "ore":
            x, y = join
            reach = max(2, radius // 2)
            height = max(3, rise // 3)
            canvas.draw_polygon(
                [(x - reach - 1, y - 2), (x - reach + 1, y - height - 1),
                 (x + 1, y - height + 1), (x + reach + 1, y - 1),
                 (x + reach, y + 2), (x + 1, y + 4), (x - 3, y + 2)],
                darken(stone, .59), filled=True,
            )
            canvas.draw_polygon(
                [(x - reach, y - 2), (x - reach + 2, y - height),
                 (x + 1, y - height + 1), (x + 2, y - 1),
                 (x + reach, y - 1), (x + reach, y + 1),
                 (x + 1, y + 3), (x - 3, y + 1)],
                darken(ore, .68), filled=True,
            )
            canvas.draw_polygon(
                [(x - reach, y - 2), (x - reach + 2, y - height),
                 (x, y - height + 1), (x + 1, y - 2), (x - 2, y)],
                ore, filled=True,
            )
            canvas.draw_polygon(
                [(x, y + 1), (x + 2, y - 1), (x + reach, y - 1),
                 (x + reach - 1, y + 1), (x + 1, y + 2)],
                brighten(ore, 1.14), filled=True,
            )
            canvas.draw_line(x - reach + 1, y - 2, x - reach + 2, y - height, brighten(ore, 1.34))
            # Rock shelves interrupt the deposit outline and hide its lower corners.
            canvas.draw_polygon(
                [(x - reach - 1, y - 1), (x - reach + 1, y - 1),
                 (x - 1, y + 1), (x - 2, y + 2), (x - reach - 1, y + 1)],
                stone, filled=True,
            )
            canvas.draw_polygon(
                [(x + 2, y + 2), (x + reach, y), (x + reach + 1, y - 1),
                 (x + reach + 1, y + 2), (x + 2, y + 4)],
                side, filled=True,
            )
    finally:
        canvas.clip_to_opaque = False


def draw_nature_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
    frame_idx: int = 0,
    total_frames: int = 1,
) -> None:
    """Render parametric nature assets: organic clustered trees, faceted rocks, and 4-stage crops."""
    _ = total_frames
    kind = str(op.get("kind", "tree")).lower()
    variants = {
        "tree": ("oak", "pine", "fruit", "sakura"),
        "rock": ("boulder", "mossy", "ore"),
        "crop": ("wheat", "berry", "carrot"),
    }
    if kind not in ("tree", "leafstudy", "bush", "grass", "rock", "flower", "crop"):
        raise ValueError(f"Unknown nature kind: {kind!r}")
    variant = str(op.get("variant", variants.get(kind, ("oak",))[0])).lower()
    if kind in variants and variant not in variants[kind]:
        raise ValueError(f"Unknown {kind} variant: {variant!r}; choose {', '.join(variants[kind])}")
    if "fracture_only" in op or "deposit" in op:
        if "fracture" not in op:
            raise ValueError("fracture_only/deposit require an explicit fracture configuration")
    if "fracture" in op:
        if kind != "rock":
            raise ValueError("fracture requires nature_rig kind:rock")
        from pixelai.fracture import draw_fracture
        draw_fracture(canvas, x, y, palette, op)
        return
    stage = max(0, min(3, int(op.get("stage", 3))))
    sway = bool(op.get("sway", False))
    draw_shadow = bool(op.get("shadow", True))
    ground_base = str(op.get("ground_base", "none")).lower()
    frame = int(op.get("frame", frame_idx)) % 4
    if "growth" in op or "trunk_only" in op:
        if kind != "tree" or variant == "pine":
            raise ValueError("growth controls currently support oak, fruit and sakura trees only")
        if "growth" not in op:
            raise ValueError("trunk_only requires an explicit growth graph configuration")

    if kind == "tree":
        drawer = conifer.draw_pine if variant == "pine" else broadleaf.draw_broadleaf
        drawer(canvas, x, y, palette, op, frame)
        return
    if kind == "leafstudy":
        leafstudy.draw_leafstudy(canvas, x, y, palette, op, frame)
        return
    if kind in ("bush", "grass"):
        (undergrowth.draw_bush if kind == "bush" else undergrowth.draw_grass)(canvas, x, y, palette, op, frame)
        return

    w = int(op.get("w", 32 if kind == "tree" else 24))
    h = int(op.get("h", 40 if kind == "tree" else 24))
    local = Canvas(w, h)
    cx = w // 2
    sway_dx = (-1, 0, 1, 0)[frame] if sway else 0

    def p(key: str, default_pal: str, fb: str) -> RGBA:
        return parse_color(op.get(key, default_pal if default_pal in palette else fb), palette)

    foliage = p("color", "grass", "#589c4c")
    foliage_l = brighten(foliage, 1.24)
    foliage_d = darken(foliage, 0.68)
    trunk = p("trunk_color", "wood", "#9c603c")
    trunk_l = brighten(trunk, 1.18)
    trunk_d = darken(trunk, 0.70)
    stone = p("color", "stone", "#8694a8")
    accent = p("accent_color", "roof" if kind == "tree" else "wheat", "#e6b84c")
    shadow_col = p("shadow_color", "shadow", "#33293a")
    shadow_col = ground_shadow_color(shadow_col)

    _draw_ground_patch(local, cx, h - 3, max(4, w // 3), 2, ground_base, palette)

    if draw_shadow:
        local.mark_shadow = True
        local.mark_no_outline = True
        sh_rx = max(4, w // 3 - 2)
        local.draw_ellipse(cx, h - 3, sh_rx, 2, shadow_col, filled=True)
        local.mark_shadow = False
        local.mark_no_outline = False

    if kind == "rock":
        moss = p("foliage_color", "grass", "#589c4c")
        _draw_rock(local, variant, int(op.get("seed", 42)), stone, moss, accent)

    elif kind == "flower":
        by = h - 4
        local.draw_rect(cx + sway_dx, by - 6, 1, 6, foliage_d, filled=True)
        local.draw_polygon([(cx - 1, by - 2), (cx - 4, by - 4), (cx - 2, by - 4)], foliage_l, filled=True)
        local.draw_polygon([(cx + 1, by - 3), (cx + 4, by - 5), (cx + 2, by - 5)], foliage, filled=True)
        petal_l = brighten(accent, 1.25)
        for px_o, py_o in ((-2, -7), (2, -7), (0, -9), (0, -5), (-1, -8), (1, -8), (-1, -6), (1, -6)):
            local.set_pixel(cx + sway_dx + px_o, by + py_o, petal_l if py_o < -7 else accent)
        local.set_pixel(cx + sway_dx, by - 7, parse_color("wheat_l", palette) if "wheat_l" in palette else (255, 240, 150, 255))

    elif kind == "crop":
        by = h - 4
        crop_col = parse_color("wheat" if variant == "wheat" else ("roof" if variant == "carrot" else "water_l"), palette)
        crop_l = brighten(crop_col, 1.25)
        crop_d = darken(crop_col, 0.74)
        soil_d = parse_color("soil_d", palette) if "soil_d" in palette else (92, 60, 40, 255)
        if stage == 0:
            for sx_off in (-4, 0, 4):
                local.set_pixel(cx + sx_off, by, soil_d)
                local.draw_rect(cx + sx_off, by - 2, 2, 2, crop_col, filled=True)
                local.set_pixel(cx + sx_off, by - 2, crop_l)
        elif stage == 1:
            for sx_off in (-3, 3):
                local.draw_rect(cx + sx_off, by - 5, 1, 5, foliage_d, filled=True)
                local.draw_rect(cx + sx_off - 2, by - 6, 2, 2, foliage_l, filled=True)
                local.draw_rect(cx + sx_off + 1, by - 6, 2, 2, foliage, filled=True)
        elif stage == 2:
            for sx_off in (-4, 0, 4):
                st_h = 8 if sx_off == 0 else 6
                local.draw_rect(cx + sx_off + sway_dx, by - st_h, 1, st_h, foliage_d, filled=True)
                local.draw_polygon([
                    (cx + sx_off + sway_dx, by - st_h + 2),
                    (cx + sx_off - 3 + sway_dx, by - st_h),
                    (cx + sx_off - 1 + sway_dx, by - st_h - 1),
                ], foliage_l, filled=True)
                local.draw_polygon([
                    (cx + sx_off + sway_dx, by - st_h + 2),
                    (cx + sx_off + 3 + sway_dx, by - st_h),
                    (cx + sx_off + 1 + sway_dx, by - st_h - 1),
                ], foliage, filled=True)
        else:
            for sx_off in (-4, 0, 4):
                tall = 13 if sx_off == 0 else 11
                lean = sway_dx + (-1 if sx_off < 0 else (1 if sx_off > 0 else 0))
                local.draw_line(cx + sx_off, by, cx + sx_off + lean, by - tall + 5, foliage_d)
                # Arching basal green leaves
                local.draw_rect(cx + sx_off - 1, by - 3, 2, 1, foliage, filled=True)
                # Lush golden grain ear or ripe crop cluster
                hx = cx + sx_off + lean
                hy = by - tall
                local.draw_rect(hx - 1, hy + 1, 3, 5, crop_col, filled=True)
                local.draw_rect(hx - 1, hy + 1, 1, 4, crop_l, filled=True)
                local.draw_rect(hx + 1, hy + 3, 1, 3, crop_d, filled=True)
                local.set_pixel(hx, hy, crop_l)

    canvas.blit(local, x, y)

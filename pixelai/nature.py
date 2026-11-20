"""Parametric cozy foliage, trees, faceted rocks, flowers, and detailed 4-stage crops."""

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


def _draw_leaf_cluster(
    canvas: Canvas, cx: int, cy: int, rx: int, ry: int, base: RGBA, hi: RGBA, sh: RGBA
) -> None:
    """Draw a textured scalloped leaf cluster with shadow rim and highlight tufts."""
    canvas.draw_ellipse(cx, cy + 1, rx, ry, sh, filled=True)
    canvas.draw_ellipse(cx, cy, rx, max(1, ry - 1), base, filled=True)
    canvas.draw_ellipse(cx - 1, cy - 1, max(1, rx - 1), max(1, ry - 1), hi, filled=True)


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
    stage = max(0, min(3, int(op.get("stage", 3))))
    sway = bool(op.get("sway", False))
    draw_shadow = bool(op.get("shadow", True))
    ground_base = str(op.get("ground_base", "none")).lower()
    frame = int(op.get("frame", frame_idx)) % 4

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
    stone_l = brighten(stone, 1.24)
    stone_d = darken(stone, 0.68)
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
        # Chiseled faceted polygonal boulder (not an oval inside an oval!)
        r = max(5, w // 4)
        ry = h - 4
        local.draw_polygon([
            (cx - r - 2, ry),
            (cx - r - 1, ry - r + 2),
            (cx - r // 2, ry - r - 1),
            (cx + r // 2, ry - r),
            (cx + r + 1, ry - r + 3),
            (cx + r + 2, ry),
        ], stone_d, filled=True)
        local.draw_polygon([
            (cx - r - 1, ry - 1),
            (cx - r, ry - r + 2),
            (cx - r // 2, ry - r - 1),
            (cx + r // 2 - 1, ry - r),
            (cx + r, ry - r + 3),
            (cx + r - 1, ry - 1),
        ], stone, filled=True)
        local.draw_polygon([
            (cx - r + 1, ry - r + 2),
            (cx - r // 2, ry - r - 1),
            (cx + 1, ry - r),
            (cx, ry - r // 2),
            (cx - r + 2, ry - r // 3),
        ], stone_l, filled=True)
        # Broad fracture planes and sparse mineral grain; no internal ink line.
        local.draw_polygon([(cx + 1, ry - r // 2), (cx + r - 1, ry - r + 3),
                            (cx + r - 2, ry - 2), (cx + 2, ry - 3)], stone_d, filled=True)
        for gy in range(ry - r + 2, ry - 1, 3):
            for gx in range(cx - r + 2, cx + r - 1, 4):
                if local.get_pixel(gx, gy) == stone:
                    local.set_pixel(gx, gy, brighten(stone, 1.10))
                    if local.get_pixel(gx + 1, gy) == stone:
                        local.set_pixel(gx + 1, gy, darken(stone, 0.90))
        if variant == "mossy":
            _draw_leaf_cluster(local, cx - 1, ry - r, max(3, r // 2), 2, foliage, foliage_l, foliage_d)
        elif variant == "ore":
            ore_l = brighten(accent, 1.35)
            ore_d = darken(accent, 0.72)
            for ox, oy in ((cx - 3, ry - r // 2 - 2), (cx + 2, ry - 4), (cx - 1, ry - 3)):
                local.draw_rect(ox, oy, 3, 2, accent, filled=True)
                local.set_pixel(ox, oy, ore_l)
                local.set_pixel(ox + 2, oy + 1, ore_d)

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

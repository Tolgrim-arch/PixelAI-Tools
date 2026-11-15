"""Parametric foliage, trees, rocks, flowers, and multi-stage crops."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color


def _draw_ground_patch(local: Canvas, cx: int, cy: int, rx: int, ry: int, kind: str, palette: dict[str, RGBA]) -> None:
    if kind == "none":
        return
    base = parse_color("soil" if kind == "soil" else "grass", palette) if (kind in palette or "grass" in palette) else (92, 168, 76, 255)
    local.mark_no_outline = True
    local.draw_ellipse(cx, cy, rx, ry, darken(base, 0.85), filled=True)
    local.draw_ellipse(cx, cy - 1, max(2, rx - 1), max(1, ry - 1), base, filled=True)
    local.mark_no_outline = False


def draw_nature_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
    frame_idx: int = 0,
    total_frames: int = 1,
) -> None:
    """Render parametric nature assets: trees, bushes, rocks, flowers, and 4-stage crops."""
    _ = total_frames
    kind = str(op.get("kind", "tree")).lower()
    variant = str(op.get("variant", "oak")).lower()
    stage = max(0, min(3, int(op.get("stage", 3))))
    sway = bool(op.get("sway", False))
    draw_shadow = bool(op.get("shadow", True))
    ground_base = str(op.get("ground_base", "none")).lower()
    frame = int(op.get("frame", frame_idx)) % 4

    w = int(op.get("w", 32 if kind == "tree" else 24))
    h = int(op.get("h", 40 if kind == "tree" else 24))
    local = Canvas(w, h)
    cx = w // 2
    sway_dx = (-1, 0, 1, 0)[frame] if sway else 0

    def p(key: str, default_pal: str, fb: str) -> RGBA:
        return parse_color(op.get(key, default_pal if default_pal in palette else fb), palette)

    foliage = p("color", "grass", "#5ca84c")
    foliage_l = brighten(foliage, 1.18)
    foliage_d = darken(foliage, 0.74)
    trunk = p("trunk_color", "wood", "#8f5c3c")
    trunk_d = darken(trunk, 0.76)
    stone = p("color", "stone", "#828c9e")
    stone_l = brighten(stone, 1.2)
    stone_d = darken(stone, 0.72)
    accent = p("accent_color", "roof" if kind == "tree" else "wheat", "#e6b84c")
    shadow_col = p("shadow_color", "shadow", "#33293a")

    _draw_ground_patch(local, cx, h - 4, max(4, w // 3), 2, ground_base, palette)

    if draw_shadow:
        local.mark_shadow = True
        local.mark_no_outline = True
        local.draw_ellipse(cx, h - 3, max(4, w // 3 - 1), 2, shadow_col, filled=True)
        local.mark_shadow = False
        local.mark_no_outline = False

    if kind == "tree":
        # Trunk
        tw = max(4, w // 6)
        th = max(8, h // 3)
        ty = h - 4 - th
        local.draw_rect(cx - tw // 2, ty, tw, th, trunk, filled=True)
        local.draw_rect(cx, ty, max(1, tw // 2), th, trunk_d, filled=True)
        if variant == "pine":
            for layer in range(3):
                ly = ty - layer * max(5, h // 7)
                rw = max(5, (w // 2 - 3) - layer * 2)
                off = sway_dx if layer > 0 else 0
                pts = [(cx + off, ly - 8), (cx + rw + off, ly + 2), (cx - rw + off, ly + 2)]
                local.draw_polygon(pts, foliage_d if layer == 0 else foliage, filled=True)
                local.draw_polygon([(cx + off, ly - 8), (cx + off, ly + 1), (cx - rw + 2 + off, ly + 1)], foliage_l, filled=True)
        else:
            cr = max(7, w // 3)
            cy_c = ty - cr // 2 + 2
            canopy = Canvas(w, h)
            canopy.draw_circle(cx + sway_dx, cy_c, cr, foliage, filled=True)
            canopy.draw_circle(cx - cr // 2 + sway_dx, cy_c + 2, max(4, cr // 2), foliage, filled=True)
            canopy.draw_circle(cx + cr // 2 + sway_dx, cy_c + 2, max(4, cr // 2), foliage, filled=True)
            canopy.clip_to_opaque = True
            canopy.draw_circle(cx + sway_dx, cy_c + cr // 2, cr, foliage_d, filled=True)
            canopy.draw_circle(cx - 2 + sway_dx, cy_c - 3, max(3, cr // 2), foliage_l, filled=True)
            canopy.clip_to_opaque = False
            if variant == "fruit":
                for fx, fy in ((cx - 4, cy_c - 1), (cx + 3, cy_c + 1), (cx, cy_c - 4)):
                    canopy.draw_rect(fx + sway_dx, fy, 2, 2, accent, filled=True)
            local.blit(canopy, 0, 0)

    elif kind == "bush":
        r = max(4, w // 4)
        by = h - 7
        local.draw_circle(cx + sway_dx, by - 1, r, foliage, filled=True)
        local.draw_circle(cx - r // 2 + sway_dx, by + 1, max(3, r - 2), foliage, filled=True)
        local.draw_circle(cx + r // 2 + sway_dx, by + 1, max(3, r - 2), foliage, filled=True)
        local.clip_to_opaque = True
        local.draw_rect(0, by + 1, w, h - by, foliage_d, filled=True)
        local.draw_circle(cx - 2 + sway_dx, by - 2, max(2, r // 2), foliage_l, filled=True)
        local.clip_to_opaque = False

    elif kind == "rock":
        r = max(4, w // 4)
        ry = h - 7
        local.draw_ellipse(cx, ry, r + 2, r, stone, filled=True)
        local.clip_to_opaque = True
        local.draw_ellipse(cx + 1, ry + 3, r + 2, r - 1, stone_d, filled=True)
        local.draw_ellipse(cx - 2, ry - 2, max(2, r // 2), max(2, r // 2), stone_l, filled=True)
        if variant == "mossy":
            local.draw_ellipse(cx - 1, ry - r + 2, max(2, r // 2), 2, foliage, filled=True)
        elif variant == "ore":
            local.draw_rect(cx - 2, ry - 2, 2, 2, accent, filled=True)
            local.draw_rect(cx + 2, ry, 2, 2, accent, filled=True)
        local.clip_to_opaque = False

    elif kind == "flower":
        by = h - 5
        local.draw_rect(cx + sway_dx, by - 5, 1, 5, foliage_d, filled=True)
        local.draw_rect(cx - 2, by - 2, 2, 1, foliage, filled=True)
        local.draw_rect(cx + 1, by - 3, 2, 1, foliage, filled=True)
        local.draw_circle(cx + sway_dx, by - 6, 2, accent, filled=True)
        local.set_pixel(cx + sway_dx, by - 6, brighten(accent, 1.25))

    elif kind == "crop":
        by = h - 5
        crop_col = parse_color("wheat" if variant == "wheat" else ("roof" if variant == "carrot" else "water_l"), palette)
        if stage == 0:
            for sx_off in (-3, 0, 3):
                local.set_pixel(cx + sx_off, by - 1, crop_col)
                local.set_pixel(cx + sx_off + 1, by, darken(crop_col, 0.78))
        elif stage == 1:
            for sx_off in (-2, 2):
                local.draw_rect(cx + sx_off, by - 3, 1, 3, foliage, filled=True)
                local.set_pixel(cx + sx_off + 1, by - 3, foliage_l)
        elif stage == 2:
            for sx_off in (-3, 0, 3):
                local.draw_rect(cx + sx_off + sway_dx, by - 6, 1, 6, foliage, filled=True)
                local.draw_rect(cx + sx_off - 1 + sway_dx, by - 5, 3, 2, foliage_l, filled=True)
        else:
            for sx_off in (-3, 0, 3):
                local.draw_rect(cx + sx_off + sway_dx, by - 8, 1, 8, foliage_d, filled=True)
                local.draw_rect(cx + sx_off - 1 + sway_dx, by - 9, 3, 4, crop_col, filled=True)
                local.set_pixel(cx + sx_off + sway_dx, by - 9, brighten(crop_col, 1.22))

    canvas.blit(local, x, y)

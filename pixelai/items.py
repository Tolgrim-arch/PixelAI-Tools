"""Parametric pixel-art items, weapons, potions, chests, and RPG loot icons."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color


def _sc(val: float, s: float) -> int:
    return max(1, int(round(val * s)))


def _draw_potion(
    local: Canvas,
    size: int,
    orientation: str,
    liquid: RGBA,
    glass: RGBA,
    cork: RGBA,
    fill_level: float,
    shine: bool,
    frame: int,
) -> None:
    s = size / 24.0
    liq_l = brighten(liquid, 1.22)
    liq_d = darken(liquid, 0.72)
    glass_l = brighten(glass, 1.18)
    cork_d = darken(cork, 0.76)

    def px(u: float) -> int:
        return int(round(u * s))

    if orientation == "diagonal":
        # 45-degree tilted RPG potion (neck top-right, bulb bottom-left)
        local.draw_circle(px(9), px(15), _sc(5.5, s), glass, filled=True)
        # Neck & rim tilted up-right
        for t in range(4):
            cx_n = px(13 + t)
            cy_n = px(11 - t)
            local.draw_circle(cx_n, cy_n, _sc(2.0, s), glass, filled=True)
        local.draw_circle(px(17), px(7), _sc(2.4, s), glass_l, filled=True)
        local.draw_circle(px(18.5), px(5.5), _sc(1.6, s), cork, filled=True)
        local.set_pixel(px(19), px(5), cork_d)

        # Liquid clipped strictly inside flask silhouette
        local.clip_to_opaque = True
        liq_r = max(1, int(round(4.6 * s * max(0.2, min(1.0, fill_level)))))
        local.draw_circle(px(9), px(15.5), liq_r, liquid, filled=True)
        local.draw_rect(px(4), px(15), px(10), px(6), liq_d, filled=True)
        local.draw_circle(px(8), px(14), max(1, liq_r // 2), liq_l, filled=True)
        if shine:
            sx_off = 1 if (frame % 4) in (1, 2) else 0
            local.draw_rect(px(6), px(12 + sx_off), max(1, _sc(1, s)), max(1, _sc(2, s)), (255, 255, 255, 255))
        local.clip_to_opaque = False
        return

    # Vertical potion (centered at x = size // 2)
    cx = size // 2
    local.draw_circle(cx, px(15), _sc(5.5, s), glass, filled=True)
    local.draw_rect(cx - _sc(2, s), px(7), _sc(4, s), _sc(5, s), glass, filled=True)
    local.draw_rect(cx - _sc(3, s), px(6), _sc(6, s), _sc(1.5, s), glass_l, filled=True)
    local.draw_rect(cx - _sc(1.5, s), px(4), _sc(3, s), _sc(2, s), cork, filled=True)
    local.draw_rect(cx - _sc(1.5, s), px(5), _sc(3, s), _sc(1, s), cork_d, filled=True)

    local.clip_to_opaque = True
    fill_h = max(1, int(round(9 * s * max(0.0, min(1.0, fill_level)))))
    if fill_h > 0:
        top_y = px(20) - fill_h
        local.draw_rect(cx - _sc(5, s), top_y, _sc(10, s), fill_h, liquid, filled=True)
        local.draw_rect(cx - _sc(5, s), px(17), _sc(10, s), _sc(4, s), liq_d, filled=True)
        local.draw_rect(cx - _sc(4, s), top_y, _sc(8, s), _sc(1, s), liq_l, filled=True)
    if shine:
        glint_y = px(12) + (1 if (frame % 4) in (1, 2) else 0)
        local.draw_rect(cx - _sc(3, s), glint_y, max(1, _sc(1, s)), _sc(3, s), (255, 255, 255, 255))
    local.clip_to_opaque = False


def _draw_sword(
    local: Canvas,
    size: int,
    orientation: str,
    blade: RGBA,
    hilt: RGBA,
    shine: bool,
    frame: int,
) -> None:
    s = size / 24.0
    blade_l = brighten(blade, 1.25)
    blade_d = darken(blade, 0.72)
    hilt_d = darken(hilt, 0.75)

    def px(u: float) -> int:
        return int(round(u * s))

    if orientation == "diagonal":
        # Blade pointing top-right, hilt bottom-left
        local.draw_line(px(7), px(17), px(19), px(5), blade)
        local.draw_line(px(8), px(17), px(19), px(6), blade_d)
        local.draw_line(px(7), px(16), px(18), px(5), blade_l)
        # Crossguard & grip
        local.draw_line(px(5), px(13), px(11), px(19), hilt)
        local.draw_line(px(4), px(20), px(7), px(17), hilt_d)
        local.draw_circle(px(4), px(20), _sc(1, s), hilt, filled=True)
        if shine:
            t = (frame % 4) * 3
            local.set_pixel(px(10 + t), px(14 - t), (255, 255, 255, 255))
        return

    cx = size // 2
    local.draw_rect(cx - _sc(1.5, s), px(4), _sc(3, s), _sc(11, s), blade, filled=True)
    local.draw_rect(cx - _sc(1.5, s), px(4), _sc(1, s), _sc(11, s), blade_l, filled=True)
    local.draw_rect(cx + _sc(0.5, s), px(5), _sc(1, s), _sc(10, s), blade_d, filled=True)
    local.set_pixel(cx, px(3), blade_l)
    # Guard, grip & pommel
    local.draw_rect(cx - _sc(4, s), px(15), _sc(8, s), _sc(2, s), hilt, filled=True)
    local.draw_rect(cx - _sc(1, s), px(17), _sc(2, s), _sc(3, s), hilt_d, filled=True)
    local.draw_rect(cx - _sc(1.5, s), px(20), _sc(3, s), _sc(1.5, s), hilt, filled=True)
    if shine:
        local.set_pixel(cx - _sc(1, s), px(6 + (frame % 4) * 2), (255, 255, 255, 255))


def _draw_chest(
    local: Canvas,
    size: int,
    wood: RGBA,
    trim: RGBA,
    state: str,
    shine: bool,
    frame: int,
) -> None:
    s = size / 24.0
    wood_d = darken(wood, 0.72)
    wood_l = brighten(wood, 1.15)
    trim_l = brighten(trim, 1.2)

    def px(u: float) -> int:
        return int(round(u * s))

    # Base box
    local.draw_rect(px(4), px(11), px(16), px(9), wood, filled=True, bevel=True)
    local.draw_rect(px(4), px(17), px(16), px(3), wood_d, filled=True)
    if state == "open":
        local.draw_rect(px(4), px(5), px(16), px(5), wood_l, filled=True, bevel=True)
        local.draw_rect(px(5), px(10), px(14), px(3), (42, 28, 36, 255), filled=True)
        local.draw_rect(px(7), px(10), px(10), px(2), trim_l, filled=True)
        if shine and (frame % 2 == 0):
            local.set_pixel(px(9), px(9), (255, 255, 255, 255))
            local.set_pixel(px(14), px(8), (255, 255, 255, 255))
    else:
        local.draw_rect(px(4), px(7), px(16), px(5), wood_l, filled=True, bevel=True)
        local.draw_rect(px(4), px(11), px(16), px(1), trim, filled=True)
    # Metal straps & lock
    local.draw_rect(px(6), px(7 if state != "open" else 11), _sc(2, s), px(13 if state != "open" else 9), trim, filled=True)
    local.draw_rect(px(16), px(7 if state != "open" else 11), _sc(2, s), px(13 if state != "open" else 9), trim, filled=True)
    local.draw_rect(px(11), px(10 if state != "open" else 12), _sc(2, s), _sc(3, s), trim_l, filled=True)


def _draw_gem(local: Canvas, size: int, color: RGBA, shine: bool, frame: int) -> None:
    s = size / 24.0
    cx, cy = size // 2, size // 2
    col_l = brighten(color, 1.28)
    col_d = darken(color, 0.72)

    def px(u: float) -> int:
        return int(round(u * s))

    pts = [(cx, cy - px(7)), (cx + px(6), cy - px(2)), (cx + px(4), cy + px(6)), (cx - px(4), cy + px(6)), (cx - px(6), cy - px(2))]
    local.draw_polygon(pts, color, filled=True)
    local.clip_to_opaque = True
    local.draw_polygon([(cx, cy - px(7)), (cx + px(3), cy - px(2)), (cx - px(3), cy - px(2))], col_l, filled=True)
    local.draw_rect(cx, cy, px(7), px(7), col_d, filled=True)
    if shine:
        gx = cx - px(2) + (1 if (frame % 4) in (1, 2) else 0)
        local.draw_rect(gx, cy - px(4), _sc(1, s), _sc(2, s), (255, 255, 255, 255))
    local.clip_to_opaque = False


def _draw_shield(local: Canvas, size: int, primary: RGBA, trim: RGBA) -> None:
    s = size / 24.0
    cx = size // 2

    def px(u: float) -> int:
        return int(round(u * s))

    pts = [(cx - px(6), px(5)), (cx + px(6), px(5)), (cx + px(6), px(13)), (cx, px(20)), (cx - px(6), px(13))]
    local.draw_polygon(pts, trim, filled=True)
    inner = [(cx - px(4), px(7)), (cx + px(4), px(7)), (cx + px(4), px(12)), (cx, px(17)), (cx - px(4), px(12))]
    local.draw_polygon(inner, primary, filled=True)
    local.draw_rect(cx - _sc(1, s), px(8), _sc(2, s), px(7), brighten(trim, 1.18), filled=True)


def _draw_key(local: Canvas, size: int, orientation: str, color: RGBA) -> None:
    s = size / 24.0
    col_l = brighten(color, 1.2)
    col_d = darken(color, 0.75)

    def px(u: float) -> int:
        return int(round(u * s))

    if orientation == "diagonal":
        local.draw_circle(px(8), px(16), _sc(3.5, s), color, filled=True)
        local.draw_circle(px(8), px(16), _sc(1.5, s), col_d, filled=True)
        local.draw_line(px(10), px(14), px(18), px(6), col_l)
        local.draw_line(px(11), px(14), px(19), px(6), color)
        local.draw_rect(px(16), px(8), _sc(2, s), _sc(2, s), col_d, filled=True)
        return

    cx = size // 2
    local.draw_circle(cx, px(7), _sc(3.5, s), col_l, filled=True)
    local.draw_circle(cx, px(7), _sc(1.5, s), col_d, filled=True)
    local.draw_rect(cx - _sc(1, s), px(10), _sc(2, s), px(9), color, filled=True)
    local.draw_rect(cx + _sc(1, s), px(15), _sc(3, s), _sc(1.5, s), col_d, filled=True)
    local.draw_rect(cx + _sc(1, s), px(18), _sc(2, s), _sc(1.5, s), col_d, filled=True)


def _draw_coin_or_apple(local: Canvas, size: int, kind: str, color: RGBA, stem: RGBA, shine: bool, frame: int) -> None:
    s = size / 24.0
    cx, cy = size // 2, size // 2

    def px(u: float) -> int:
        return int(round(u * s))

    if kind == "coin":
        rx = max(2, _sc(5, s) - (2 if (frame % 4) in (1, 3) else 0))
        local.draw_ellipse(cx, cy, rx, _sc(6, s), color, filled=True)
        local.clip_to_opaque = True
        local.draw_ellipse(cx - 1, cy - 1, max(1, rx - 1), _sc(4, s), brighten(color, 1.22), filled=True)
        local.draw_rect(cx, cy - _sc(2, s), max(1, rx // 3), _sc(5, s), darken(color, 0.72), filled=True)
        if shine:
            local.set_pixel(cx - max(1, rx // 2), cy - _sc(3, s), (255, 255, 255, 255))
        local.clip_to_opaque = False
        return

    # Apple
    local.draw_circle(cx, cy + px(1), _sc(6, s), color, filled=True)
    local.clip_to_opaque = True
    local.draw_circle(cx + px(2), cy + px(3), _sc(5, s), darken(color, 0.75), filled=True)
    local.draw_circle(cx - px(2), cy - px(1), _sc(2, s), brighten(color, 1.2), filled=True)
    local.clip_to_opaque = False
    local.draw_rect(cx, cy - px(6), _sc(1, s), _sc(3, s), stem, filled=True)
    local.draw_rect(cx + _sc(1, s), cy - px(5), _sc(3, s), _sc(2, s), parse_color("grass", {"grass": (92, 168, 76, 255)}), filled=True)


def draw_item_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
    frame_idx: int = 0,
    total_frames: int = 1,
) -> None:
    """Render a parametric RPG item/loot icon with optional orientation and world shadow."""
    _ = total_frames
    kind = str(op.get("kind", "potion")).lower()
    orientation = str(op.get("orientation", "vertical")).lower()
    size = max(16, int(op.get("size", 24)))
    shine = bool(op.get("shine", True))
    draw_shadow = bool(op.get("shadow", False))
    frame = int(op.get("frame", frame_idx))

    local = Canvas(size, size)

    if draw_shadow:
        sh_col = parse_color(op.get("shadow_color", "shadow" if "shadow" in palette else "#33293a"), palette)
        local.mark_shadow = True
        local.mark_no_outline = True
        local.draw_ellipse(size // 2, size - max(2, size // 10), max(3, size // 4), max(1, size // 12), sh_col, filled=True)
        local.mark_shadow = False
        local.mark_no_outline = False

    def col(key: str, default_pal: str, fallback_hex: str) -> RGBA:
        return parse_color(op.get(key, default_pal if default_pal in palette else fallback_hex), palette)

    if kind == "potion":
        _draw_potion(
            local,
            size,
            orientation,
            col("color", "roof", "#c24b38"),
            col("secondary_color", "water_l", "#b4e3f2"),
            col("cork_color", "wood", "#9c603c"),
            float(op.get("fill_level", 0.78)),
            shine,
            frame,
        )
    elif kind == "sword":
        _draw_sword(local, size, orientation, col("color", "stone_l", "#c5d1e0"), col("secondary_color", "wheat", "#d99b38"), shine, frame)
    elif kind == "chest":
        _draw_chest(local, size, col("color", "wood", "#9c603c"), col("secondary_color", "wheat", "#e0ab43"), str(op.get("state", "closed")).lower(), shine, frame)
    elif kind == "gem":
        _draw_gem(local, size, col("color", "water", "#4fa4c4"), shine, frame)
    elif kind == "shield":
        _draw_shield(local, size, col("color", "water_d", "#326496"), col("secondary_color", "stone_l", "#c5d1e0"))
    elif kind == "key":
        _draw_key(local, size, orientation, col("color", "wheat", "#e0ab43"))
    else:
        _draw_coin_or_apple(local, size, kind, col("color", "wheat" if kind == "coin" else "roof", "#e0ab43"), col("secondary_color", "wood_d", "#6e422c"), shine, frame)

    canvas.blit(local, x, y)

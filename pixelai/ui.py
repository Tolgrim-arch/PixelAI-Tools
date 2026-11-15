"""Parametric 9-slice UI panels, HUD bars, hearts, slots, and multi-state buttons."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color

_THEMES: dict[str, tuple[RGBA, RGBA, RGBA, RGBA]] = {
    "wood": ((143, 92, 60, 255), (186, 128, 86, 255), (92, 54, 36, 255), (235, 214, 178, 255)),
    "stone": ((118, 128, 146, 255), (160, 172, 192, 255), (72, 78, 94, 255), (48, 52, 66, 255)),
    "gold": ((214, 158, 56, 255), (248, 206, 96, 255), (148, 96, 32, 255), (64, 42, 34, 255)),
    "paper": ((236, 222, 192, 255), (252, 244, 224, 255), (184, 158, 124, 255), (246, 236, 214, 255)),
    "dark": ((58, 52, 72, 255), (92, 84, 114, 255), (34, 30, 44, 255), (28, 24, 36, 255)),
}


def draw_ui_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Render HUD/UI components: panel, bar, button, heart, or inventory slot."""
    kind = str(op.get("kind", "panel")).lower()
    theme = str(op.get("theme", "wood")).lower()
    state = str(op.get("state", "normal")).lower()
    base, light, dark, inner = _THEMES.get(theme, _THEMES["wood"])
    if "color" in op:
        base = parse_color(op["color"], palette)
        light = brighten(base, 1.2)
        dark = darken(base, 0.72)

    w = int(op.get("w", 48 if kind in ("panel", "bar", "button") else 16))
    h = int(op.get("h", 32 if kind == "panel" else (12 if kind in ("bar", "button") else 16)))
    local = Canvas(w, h)

    if kind == "panel":
        local.draw_rect(0, 0, w, h, base, filled=True, bevel=True)
        if bool(op.get("inner_fill", True)) and w > 6 and h > 6:
            local.draw_rect(2, 2, w - 4, h - 4, dark, filled=True)
            local.draw_rect(3, 3, w - 6, h - 6, inner, filled=True)
        # Corner rivets / trim accents
        for rx, ry in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
            local.set_pixel(rx, ry, light)

    elif kind == "slot":
        bg = brighten(inner, 1.12) if state == "selected" else inner
        border = parse_color("wheat_l" if "wheat_l" in palette else "#ffe478", palette) if state == "selected" else base
        local.draw_rect(0, 0, w, h, border, filled=True, bevel=True)
        local.draw_rect(2, 2, max(2, w - 4), max(2, h - 4), bg, filled=True, recessed=True)

    elif kind == "button":
        dy = 1 if state == "pressed" else 0
        col = brighten(base, 1.15) if state == "hover" else (dark if state == "pressed" else base)
        local.draw_rect(0, dy, w, max(4, h - dy), col, filled=True, bevel=(state != "pressed"), recessed=(state == "pressed"))
        local.draw_rect(2, 2 + dy, max(2, w - 4), max(2, h - 5), light if state == "hover" else base, filled=True)

    elif kind == "bar":
        fill_ratio = max(0.0, min(1.0, float(op.get("fill", 0.75))))
        fill_col = parse_color(op.get("fill_color", "roof" if "roof" in palette else "#c24b38"), palette)
        local.draw_rect(0, 0, w, h, base, filled=True, bevel=True)
        local.draw_rect(2, 2, max(2, w - 4), max(2, h - 4), dark, filled=True, recessed=True)
        inner_w = max(0, int(round((w - 4) * fill_ratio)))
        if inner_w > 0 and h > 4:
            local.draw_rect(2, 2, inner_w, h - 4, fill_col, filled=True)
            local.draw_rect(2, 2, inner_w, 1, brighten(fill_col, 1.24), filled=True)
            if bool(op.get("segmented", True)):
                for sx in range(6, inner_w, 6):
                    local.draw_line(2 + sx, 2, 2 + sx, h - 3, darken(fill_col, 0.75))

    elif kind == "heart":
        red = parse_color(op.get("color", "roof" if "roof" in palette else "#d4423b"), palette)
        red_l = brighten(red, 1.25)
        empty_c = parse_color("stone_d" if "stone_d" in palette else "#4e5263", palette)
        cx = w // 2
        # Heart silhouette via pixel rows centered at (cx, h//2)
        rows = [
            " .oo..oo. ",
            ".oooooooo.",
            "oooooooooo",
            "oooooooooo",
            ".oooooooo.",
            "..oooooo..",
            "...oooo...",
            "....oo....",
        ]
        ox = max(0, cx - 5)
        oy = max(0, h // 2 - 4)
        for ry_i, row in enumerate(rows):
            for rx_i, ch in enumerate(row):
                if ch != "o":
                    continue
                is_left = rx_i < 5
                if state == "empty" or (state == "half" and not is_left):
                    c = empty_c
                elif ry_i in (1, 2) and rx_i in (2, 3):
                    c = red_l
                else:
                    c = red
                local.set_pixel(ox + rx_i, oy + ry_i, c)

    canvas.blit(local, x, y)

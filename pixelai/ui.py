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

_HEART_ROWS = (
    " .oo..oo. ",
    ".oooooooo.",
    "oooooooooo",
    "oooooooooo",
    ".oooooooo.",
    "..oooooo..",
    "...oooo...",
    "....oo....",
)


def _draw_single_heart(
    local: Canvas,
    ox: int,
    oy: int,
    state: str,
    red: RGBA,
    red_l: RGBA,
    empty_c: RGBA,
    outline_c: RGBA,
) -> None:
    """Draw a single 10x8 heart icon with clean crisp rim and highlight."""
    for ry_i, row in enumerate(_HEART_ROWS):
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
    # 1px crisp outer rim on heart pixels
    for ry_i, row in enumerate(_HEART_ROWS):
        for rx_i, ch in enumerate(row):
            if ch != "o":
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = rx_i + dx, ry_i + dy
                if not (0 <= ny < len(_HEART_ROWS) and 0 <= nx < len(_HEART_ROWS[0]) and _HEART_ROWS[ny][nx] == "o"):
                    local.set_pixel(ox + nx, oy + ny, outline_c)


def draw_ui_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Render HUD/UI components: panel, bar, button, heart(s), or inventory slot."""
    kind = str(op.get("kind", op.get("component", "panel"))).lower()
    theme = str(op.get("theme", "wood")).lower()
    state = str(op.get("state", "normal")).lower()
    if op.get("selected", False) and state == "normal":
        state = "selected"
    base, light, dark, inner = _THEMES.get(theme, _THEMES["wood"])
    if "color" in op and kind != "bar":
        base = parse_color(op["color"], palette)
        light = brighten(base, 1.2)
        dark = darken(base, 0.72)

    default_w = 48 if kind in ("panel", "bar", "button") else (int(op.get("count", 3)) * 13 if kind == "hearts" else 16)
    default_h = 32 if kind == "panel" else (12 if kind in ("bar", "button", "hearts") else 16)
    w = int(op.get("w", default_w))
    h = int(op.get("h", default_h))
    local = Canvas(w, h)

    if kind == "panel":
        local.draw_rect(0, 0, w, h, base, filled=True, bevel=True)
        if bool(op.get("inner_fill", True)) and w > 6 and h > 6:
            local.draw_rect(2, 2, w - 4, h - 4, dark, filled=True)
            local.draw_rect(3, 3, w - 6, h - 6, inner, filled=True)
        for rx, ry in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
            local.set_pixel(rx, ry, light)

    elif kind == "slot":
        bg = brighten(inner, 1.12) if state == "selected" else inner
        border = parse_color("wheat_l" if "wheat_l" in palette else "#ffe478", palette) if state == "selected" else base
        local.draw_rect(0, 0, w, h, border, filled=True, bevel=True)
        local.draw_rect(2, 2, max(2, w - 4), max(2, h - 4), bg, filled=True, recessed=True)

    elif kind == "button":
        dy = 1 if state == "pressed" else 0
        col = brighten(base, 1.18) if state == "hover" else (dark if state == "pressed" else base)
        local.draw_rect(0, dy, w, max(4, h - dy), col, filled=True, bevel=(state != "pressed"), recessed=(state == "pressed"))
        fill_mid = brighten(light, 1.1) if state == "hover" else (dark if state == "pressed" else base)
        local.draw_rect(2, 2 + dy, max(2, w - 4), max(2, h - 5), fill_mid, filled=True)
        # Clean centered button gloss / glyph bar
        if w >= 16 and h >= 10:
            local.draw_line(4, 2 + dy, w - 5, 2 + dy, brighten(fill_mid, 1.25))

    elif kind == "bar":
        fill_ratio = max(0.0, min(1.0, float(op.get("fill", op.get("value", 0.75)))))
        fill_col = parse_color(op.get("fill_color", op.get("color", "roof" if "roof" in palette else "#c24b38")), palette)
        local.draw_rect(0, 0, w, h, base, filled=True, bevel=True)
        local.draw_rect(1, 1, max(2, w - 2), max(2, h - 2), dark, filled=True, recessed=True)
        inner_w = max(0, int(round((w - 4) * fill_ratio)))
        if inner_w > 0 and h > 4:
            local.draw_rect(2, 2, inner_w, h - 4, fill_col, filled=True)
            local.draw_rect(2, 2, inner_w, 1, brighten(fill_col, 1.24), filled=True)
            if bool(op.get("segmented", True)):
                for sx in range(6, inner_w, 6):
                    local.draw_line(2 + sx, 2, 2 + sx, h - 3, darken(fill_col, 0.75))

    elif kind in ("heart", "hearts"):
        red = parse_color(op.get("color", "roof" if "roof" in palette else "#d4423b"), palette)
        red_l = brighten(red, 1.28)
        empty_c = parse_color("stone_d" if "stone_d" in palette else "#4e5263", palette)
        outline_c = parse_color("ink" if "ink" in palette else "#21181b", palette)
        if kind == "heart":
            ox = max(1, w // 2 - 5)
            oy = max(1, h // 2 - 4)
            _draw_single_heart(local, ox, oy, state, red, red_l, empty_c, outline_c)
        else:
            count = max(1, int(op.get("count", 3)))
            filled = float(op.get("filled", count))
            oy = max(1, h // 2 - 4)
            for idx in range(count):
                rem = filled - idx
                st = "full" if rem >= 0.75 else ("half" if rem >= 0.25 else "empty")
                _draw_single_heart(local, 1 + idx * 13, oy, st, red, red_l, empty_c, outline_c)

    canvas.blit(local, x, y)

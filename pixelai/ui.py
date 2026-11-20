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


def _metal_rails(local: Canvas, frame: int, base: RGBA, light: RGBA, dark: RGBA) -> None:
    """Layer a chased gold rail with structural ribs and sparse, varied inlays."""
    for vertical, length in ((False, local.width), (True, local.height)):
        across = local.width if vertical else local.height
        for far in (False, True):
            def point(along, depth):
                depth = across - 1 - depth if far else depth
                return (depth, along) if vertical else (along, depth)

            def line(start, end, depth, color):
                local.draw_line(*point(start, depth), *point(end, depth), color)

            # A raised spine, dark undercut, and narrow light-catching flutes
            # give the metal volume before ornament is added.
            for depth, tone in ((1, dark), (2, base), (3, light),
                                (4, base), (5, base), (frame - 2, dark)):
                if 0 <= depth < frame:
                    line(frame + 2, length - frame - 3, depth,
                         dark if far and depth in (2, 3) else tone)
            # Fine chased grooves, divided into long panels by raised collars.
            span = length - 2 * (frame + 5)
            if span > 18:
                for fraction in (.32, .68):
                    at = round(frame + 5 + span * fraction)
                    mid = frame // 2
                    for delta in (-1, 0, 1):
                        line(at + delta, at + delta, mid + (delta == 1),
                             darken(base, .72) if delta == 0 else brighten(base, 1.2))


def _draw_panel(local: Canvas, theme: str, colors: tuple[RGBA, RGBA, RGBA, RGBA],
                frame: int, filled: bool) -> None:
    """Build material framing at final resolution; details never scale with width."""
    base, light, dark, inner = colors
    w, h = local.width, local.height
    cut = max(1, frame // 2)
    local.draw_polygon([(cut, 0), (w - 1 - cut, 0), (w - 1, cut),
                        (w - 1, h - 1 - cut), (w - 1 - cut, h - 1),
                        (cut, h - 1), (0, h - 1 - cut), (0, cut)], base, filled=True)
    local.draw_line(cut, 0, w - 1 - cut, 0, light)
    local.draw_line(0, cut, 0, h - 1 - cut, light)
    local.draw_line(cut, h - 1, w - 1 - cut, h - 1, darken(base, 0.88))
    local.draw_line(w - 1, cut, w - 1, h - 1 - cut, darken(base, 0.88))
    # Recess is a broad plane with a one-pixel reflected lip, not a dark outline.
    local.draw_rect(frame - 1, frame - 1, w - 2 * frame + 2, h - 2 * frame + 2,
                    brighten(base, 1.1), filled=True)
    local.draw_rect(frame, frame, w - 2 * frame, h - 2 * frame,
                    inner if filled else (0, 0, 0, 0), filled=True)
    if theme == "gold" and frame >= 6:
        _metal_rails(local, frame, base, light, dark)
    pitch = {"wood": 17, "stone": 16, "gold": 14, "paper": 21, "dark": 18}[theme]
    mid = max(1, frame // 2)
    for tx in range(frame + 4, w - frame - 4, pitch):
        for ty in (mid, h - 1 - mid):
            if theme == "wood":
                local.draw_line(tx, ty, min(tx + 6, w - frame - 1), ty, brighten(base, 1.12))
                if frame >= 5:
                    local.draw_line(tx + 2, ty + 1, tx + 4, ty + 1, brighten(base, 1.06))
            elif theme == "stone":
                local.draw_line(tx, 1 if ty == mid else h - frame + 1,
                                tx, frame - 2 if ty == mid else h - 2, brighten(base, 1.16))
                local.set_pixel(tx + 3, ty, light)
            elif theme == "gold":
                if frame >= 6:
                    continue
                local.draw_line(tx - 1, ty, tx, ty - 1, light)
                local.draw_line(tx, ty - 1, tx + 1, ty, light)
                local.set_pixel(tx, ty + 1, brighten(base, 1.13))
            elif theme == "paper":
                local.draw_line(tx, ty, tx + 3, ty, brighten(base, 1.05))
            else:
                # Illuminated runes are inset into the frame, leaving content clear.
                local.draw_line(tx - 1, ty + 1, tx, ty - 1, light)
                local.draw_line(tx, ty - 1, tx + 1, ty + 1, light)
                local.set_pixel(tx, ty, light)
    for cx, cy in ((mid, mid), (w - 1 - mid, mid),
                   (mid, h - 1 - mid), (w - 1 - mid, h - 1 - mid)):
        if theme == "wood":
            local.set_pixel(cx, cy, (214, 192, 146, 255))
            if frame >= 5:
                local.set_pixel(cx + 1, cy, brighten(base, 1.18))
                local.set_pixel(cx, cy - 1, (245, 227, 183, 255))
        elif theme == "gold":
            # Corner fittings read as layered brackets around a faceted inset,
            # rather than four identical flat diamond badges.
            inward_x = 1 if cx < w // 2 else -1
            inward_y = 1 if cy < h // 2 else -1
            reach = max(2, frame - 3)
            local.draw_line(cx, cy, cx + inward_x * reach, cy, light)
            local.draw_line(cx, cy, cx, cy + inward_y * reach, dark)
            local.draw_line(cx + inward_x, cy + inward_y,
                            cx + inward_x * max(1, reach - 1), cy + inward_y,
                            light)
            # Small dark socket and a single clipped glint make the fitting
            # read as recessed metalwork; jewel color is reserved for a hero.
            local.draw_rect(cx - 1, cy - 1, 2, 2, dark, filled=True)
            local.set_pixel(cx - 1, cy - 1, light)
        elif theme == "paper":
            inward_x = 1 if cx < w // 2 else -1
            inward_y = 1 if cy < h // 2 else -1
            local.draw_polygon([(cx - inward_x, cy - inward_y),
                                (cx + inward_x * max(1, frame // 2), cy - inward_y),
                                (cx - inward_x, cy + inward_y * max(1, frame // 2))],
                               light, filled=True)
        elif theme == "stone":
            local.draw_line(cx - 1, cy, cx + 1, cy, light)
        else:
            local.set_pixel(cx, cy, brighten(light, 1.3))


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
    if kind not in {"panel", "slot", "button", "bar", "heart", "hearts"}:
        raise ValueError(f"Unknown UI kind: {kind}")
    if theme not in _THEMES:
        raise ValueError(f"Unknown UI theme: {theme}")
    if w < 8 or h < 8:
        raise ValueError("UI components require w and h of at least 8 pixels")
    local = Canvas(w, h)

    if kind == "panel":
        frame = int(op.get("frame_width", 3))
        if not 3 <= frame <= 12 or 2 * frame >= min(w, h):
            raise ValueError("frame_width must be 3..12 and leave a positive content area")
        _draw_panel(local, theme, (base, light, dark, inner), frame,
                    bool(op.get("inner_fill", True)))

    elif kind == "slot":
        bg = brighten(inner, 1.12) if state == "selected" else inner
        border = parse_color("wheat_l" if "wheat_l" in palette else "#ffe478", palette) if state == "selected" else base
        local.draw_rect(0, 0, w, h, border, filled=True, bevel=True)
        local.draw_rect(2, 2, max(2, w - 4), max(2, h - 4), bg, filled=True, recessed=True)

    elif kind == "button":
        dy = 1 if state == "pressed" else 0
        col = light if state == "hover" else (dark if state == "pressed" else base)
        local.draw_rect(0, dy, w, max(4, h - dy), col, filled=True,
                        bevel=(state != "pressed"), recessed=(state == "pressed") )
        fill_mid = light if state == "hover" else (dark if state == "pressed" else base)
        # Beveled inset face surrounded by a distinct narrow metal ferrule.
        trim = (61, 123, 124, 255) if state == "hover" else darken(base, .52)
        local.draw_rect(2, 2 + dy, max(2, w - 4), max(2, h - 5), trim, filled=True)
        local.draw_rect(3, 3 + dy, max(2, w - 6), max(2, h - 7), fill_mid,
                        filled=True, bevel=(state != "pressed"),
                        recessed=(state == "pressed"))
        if w >= 16 and h >= 10:
            # Tapered center crest plus paired end catches; controls now have
            # a built face, not a generic gloss stripe.
            mid = w // 2
            crest = light if state != "pressed" else dark
            local.draw_polygon([(mid - 3, 4 + dy), (mid, 3 + dy),
                                (mid + 3, 4 + dy), (mid, 5 + dy)], crest, filled=True)
            for ax in (4, w - 5):
                local.set_pixel(ax, h // 2 + dy, light if state != "pressed" else dark)

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

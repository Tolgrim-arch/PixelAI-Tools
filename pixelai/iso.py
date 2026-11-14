"""2:1 Isometric projection primitives and 3D structure sorter for pixelai-tools."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, parse_color


def _darken(c: RGBA, factor: float = 0.72) -> RGBA:
    return (
        max(0, int(c[0] * factor)),
        max(0, int(c[1] * factor)),
        max(0, int(c[2] * factor)),
        c[3],
    )


def _brighten(c: RGBA, factor: float = 1.16) -> RGBA:
    return (
        min(255, int(c[0] * factor + 8)),
        min(255, int(c[1] * factor + 8)),
        min(255, int(c[2] * factor + 8)),
        c[3],
    )


def draw_iso_tile(
    canvas: Canvas,
    cx: int,
    cy: int,
    rx: int,
    ry: int,
    color: RGBA,
    border: RGBA | None = None,
) -> None:
    """Draw a 2:1 isometric diamond tile centered at (cx, cy)."""
    if rx <= 0 or ry <= 0:
        return
    for dy in range(-ry, ry + 1):
        half_w = int(round(rx * (1.0 - abs(dy) / ry)))
        canvas.draw_line(cx - half_w, cy + dy, cx + half_w, cy + dy, color)
        if border is not None:
            canvas.set_pixel(cx - half_w, cy + dy, border)
            canvas.set_pixel(cx + half_w, cy + dy, border)


def draw_iso_box(
    canvas: Canvas,
    cx: int,
    cy: int,
    rx: int,
    ry: int,
    h: int,
    top_color: RGBA,
    left_color: RGBA,
    right_color: RGBA,
    edge_color: RGBA | None = None,
    bevel: bool = True,
    ground_shadow: int = 0,
) -> None:
    """Draw a lineless 2:1 isometric 3D box with specular bevels and optional ground shadow."""
    _ = edge_color  # Internal outlines are disabled by design; use lineless bevels
    if rx <= 0 or ry <= 0 or h < 0:
        return

    if ground_shadow > 0 and h > 0:
        for dx in range(rx + 1):
            y_base = cy + ry - int(round(ry * dx / rx)) + h - 1
            for s in range(1, ground_shadow + 1):
                gx, gy = cx + dx + s, y_base + (s // 2)
                existing = canvas.get_pixel(gx, gy)
                if existing[3] > 0:
                    canvas.set_pixel(gx, gy, _darken(existing, 0.75))

    if h > 0:
        for dx in range(rx + 1):
            y_left = cy + int(round(ry * dx / rx))
            canvas.draw_line(cx - rx + dx, y_left, cx - rx + dx, y_left + h - 1, left_color)
            y_right = cy + ry - int(round(ry * dx / rx))
            canvas.draw_line(cx + dx, y_right, cx + dx, y_right + h - 1, right_color)

    draw_iso_tile(canvas, cx, cy, rx, ry, top_color, border=None)

    if bevel and h > 0:
        hl_top = _brighten(top_color, 1.12)
        hl_left = _brighten(left_color, 1.14)
        for dx in range(rx + 1):
            yl = cy + int(round(ry * dx / rx))
            yr = cy + ry - int(round(ry * dx / rx))
            canvas.set_pixel(cx - rx + dx, yl, hl_top)
            canvas.set_pixel(cx + dx, yr, hl_top)
        canvas.draw_line(cx, cy + ry + 1, cx, cy + ry + h - 1, hl_left)


def _apply_eave_shadow(canvas: Canvas, cx: int, cy: int, rx: int, ry: int) -> None:
    """Darken 1px directly under the front-left and front-right roof eaves."""
    for dx in range(rx + 1):
        yl = cy + int(round(ry * dx / rx)) + 1
        yr = cy + ry - int(round(ry * dx / rx)) + 1
        cl = canvas.get_pixel(cx - rx + dx, yl)
        if cl[3] > 0:
            canvas.set_pixel(cx - rx + dx, yl, _darken(cl, 0.72))
        cr = canvas.get_pixel(cx + dx, yr)
        if cr[3] > 0:
            canvas.set_pixel(cx + dx, yr, _darken(cr, 0.72))


def draw_iso_roof(
    canvas: Canvas,
    cx: int,
    cy: int,
    rx: int,
    ry: int,
    h: int,
    left_color: RGBA,
    right_color: RGBA,
    style: str = "pyramid",
    gable_color: RGBA | None = None,
    ridge_color: RGBA | None = None,
    eave_shadow: bool = True,
    bevel: bool = True,
) -> None:
    """Draw a lineless pitched isometric roof ('pyramid', 'gable_left', or 'gable_right')."""
    _ = ridge_color  # Internal dark ridges are disabled; use lineless specular bevels
    if rx <= 0 or ry <= 0 or h <= 0:
        return
    apex_y = cy - h

    if eave_shadow:
        _apply_eave_shadow(canvas, cx, cy, rx, ry)

    if style == "pyramid":
        canvas.draw_polygon(
            [(cx - rx, cy), (cx, cy + ry), (cx, apex_y)], left_color
        )
        canvas.draw_polygon(
            [(cx + rx, cy), (cx, cy + ry), (cx, apex_y)], right_color
        )
        if bevel:
            canvas.draw_line(cx, apex_y, cx, cy + ry, _brighten(left_color, 1.12))

    elif style == "gable_left":
        g_col = gable_color or left_color
        half_rx = rx // 2
        half_ry = max(1, half_rx // 2)
        front_cx, front_cy = cx - half_rx, cy + ry - half_ry
        back_cx, back_cy = cx + rx - half_rx, cy - half_ry
        canvas.draw_polygon(
            [
                (front_cx, front_cy - h),
                (back_cx, back_cy - h),
                (cx + rx, cy),
                (cx, cy + ry),
            ],
            right_color,
        )
        canvas.draw_polygon(
            [(cx - rx, cy), (cx, cy + ry), (front_cx, front_cy - h)],
            g_col,
        )
        if bevel:
            hl = _brighten(g_col, 1.14)
            canvas.draw_line(front_cx, front_cy - h, back_cx, back_cy - h, hl)
            canvas.draw_line(cx, cy + ry, front_cx, front_cy - h, hl)

    elif style == "gable_right":
        g_col = gable_color or right_color
        half_rx = rx // 2
        half_ry = max(1, half_rx // 2)
        front_cx, front_cy = cx + half_rx, cy + ry - half_ry
        back_cx, back_cy = cx - rx + half_rx, cy - half_ry
        canvas.draw_polygon(
            [
                (back_cx, back_cy - h),
                (front_cx, front_cy - h),
                (cx, cy + ry),
                (cx - rx, cy),
            ],
            left_color,
        )
        canvas.draw_polygon(
            [(cx, cy + ry), (cx + rx, cy), (front_cx, front_cy - h)],
            g_col,
        )
        if bevel:
            hl = _brighten(left_color, 1.14)
            canvas.draw_line(back_cx, back_cy - h, front_cx, front_cy - h, hl)
            canvas.draw_line(cx, cy + ry, front_cx, front_cy - h, hl)
    else:
        raise ValueError(f"Unknown iso_roof style: {style!r}")


def draw_iso_wall_rect(
    canvas: Canvas,
    face: str,
    x: int,
    y: int,
    w: int,
    h: int,
    color: RGBA,
    border: RGBA | None = None,
    arch: bool = False,
    recessed: bool = True,
) -> None:
    """Draw a rectangle sheared to a 2:1 isometric 'left' or 'right' wall with lineless recessed depth by default."""
    _ = border  # Internal dark borders disabled in favor of lineless recessed depth
    if w <= 0 or h <= 0:
        return
    slope = 1 if face == "left" else -1
    recess_col = _darken(color, 0.68)
    for dx in range(w):
        sy = y + (dx * slope) // 2
        top_offset = 1 if (arch and w >= 3 and (dx == 0 or dx == w - 1)) else 0
        y0 = sy + top_offset
        y1 = sy + h - 1
        if y0 <= y1:
            canvas.draw_line(x + dx, y0, x + dx, y1, color)
            if recessed:
                canvas.set_pixel(x + dx, y0, recess_col)
                side_dx = 0 if face == "left" else w - 1
                if dx == side_dx:
                    canvas.draw_line(x + dx, y0, x + dx, y1, recess_col)


def draw_iso_structure(
    canvas: Canvas,
    origin_x: int,
    origin_y: int,
    items: list[dict[str, Any]],
    palette: dict[str, RGBA],
    step_x: int = 2,
    step_y: int = 1,
    default_bevel: bool = True,
    default_ground_shadow: int = 2,
) -> None:
    """Sort and render 3D lineless isometric boxes/roofs by depth (gx + gy, gz)."""
    sorted_items = sorted(
        items,
        key=lambda it: (
            float(it.get("gx", 0)) + float(it.get("gy", 0)),
            float(it.get("gz", 0)),
        ),
    )
    for it in sorted_items:
        gx = int(it.get("gx", 0))
        gy = int(it.get("gy", 0))
        gz = int(it.get("gz", 0))
        rx = int(it["rx"])
        ry = int(it.get("ry", max(1, rx // 2)))
        h = int(it["h"])
        cx = origin_x + (gx - gy) * step_x
        cy = origin_y + (gx + gy) * step_y - gz

        kind = it.get("type", "box")
        bevel = bool(it.get("bevel", default_bevel))
        if kind == "box":
            g_shadow = int(it.get("ground_shadow", default_ground_shadow if gz == 0 else 0))
            draw_iso_box(
                canvas,
                cx,
                cy,
                rx,
                ry,
                h,
                parse_color(it["top"], palette),
                parse_color(it["left"], palette),
                parse_color(it["right"], palette),
                bevel=bevel,
                ground_shadow=g_shadow,
            )
        elif kind == "roof":
            gable = parse_color(it["gable"], palette) if "gable" in it else None
            draw_iso_roof(
                canvas,
                cx,
                cy,
                rx,
                ry,
                h,
                parse_color(it["left"], palette),
                parse_color(it["right"], palette),
                style=it.get("style", "pyramid"),
                gable_color=gable,
                eave_shadow=bool(it.get("eave_shadow", True)),
                bevel=bevel,
            )
        else:
            raise ValueError(f"Unknown iso_structure item type: {kind!r}")

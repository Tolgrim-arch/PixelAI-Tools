"""2:1 Isometric projection primitives for pixelai-tools."""

from pixelai.canvas import Canvas
from pixelai.color import RGBA


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
) -> None:
    """Draw a 2:1 isometric 3D box with optional crease/edge lines."""
    if rx <= 0 or ry <= 0 or h < 0:
        return

    # Extruded side faces first so top diamond cleanly caps them
    if h > 0:
        for dx in range(rx + 1):
            y_left = cy + int(round(ry * dx / rx))
            canvas.draw_line(cx - rx + dx, y_left, cx - rx + dx, y_left + h - 1, left_color)
            y_right = cy + ry - int(round(ry * dx / rx))
            canvas.draw_line(cx + dx, y_right, cx + dx, y_right + h - 1, right_color)

    draw_iso_tile(canvas, cx, cy, rx, ry, top_color, border=edge_color)

    if edge_color is not None and h > 0:
        # Vertical outer & center edges + bottom V edges
        canvas.draw_line(cx - rx, cy, cx - rx, cy + h - 1, edge_color)
        canvas.draw_line(cx + rx, cy, cx + rx, cy + h - 1, edge_color)
        canvas.draw_line(cx, cy + ry, cx, cy + ry + h - 1, edge_color)
        for dx in range(rx + 1):
            yl = cy + int(round(ry * dx / rx)) + h - 1
            yr = cy + ry - int(round(ry * dx / rx)) + h - 1
            canvas.set_pixel(cx - rx + dx, yl, edge_color)
            canvas.set_pixel(cx + dx, yr, edge_color)


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
) -> None:
    """Draw a pitched isometric roof ('pyramid', 'gable_left', or 'gable_right')."""
    if rx <= 0 or ry <= 0 or h <= 0:
        return
    apex_y = cy - h

    if style == "pyramid":
        # Left front triangle: (cx - rx, cy) -> (cx, cy + ry) -> (cx, apex_y)
        canvas.draw_polygon(
            [(cx - rx, cy), (cx, cy + ry), (cx, apex_y)], left_color
        )
        # Right front triangle: (cx + rx, cy) -> (cx, cy + ry) -> (cx, apex_y)
        canvas.draw_polygon(
            [(cx + rx, cy), (cx, cy + ry), (cx, apex_y)], right_color
        )
        if ridge_color is not None:
            canvas.draw_line(cx, apex_y, cx, cy + ry, ridge_color)
            canvas.draw_line(cx - rx, cy, cx, apex_y, ridge_color)
            canvas.draw_line(cx + rx, cy, cx, apex_y, ridge_color)

    elif style == "gable_left":
        # Front-left is triangular gable wall; right slope is visible roof plane
        g_col = gable_color or left_color
        front_cx, front_cy = cx - rx // 2, cy + ry // 2
        back_cx, back_cy = cx + rx // 2, cy - ry // 2
        # Right sloped roof quad: (front_cx, front_cy - h) -> (back_cx, back_cy - h) -> (cx + rx, cy) -> (cx, cy + ry)
        canvas.draw_polygon(
            [
                (front_cx, front_cy - h),
                (back_cx, back_cy - h),
                (cx + rx, cy),
                (cx, cy + ry),
            ],
            right_color,
        )
        # Left gable triangle: (cx - rx, cy) -> (cx, cy + ry) -> (front_cx, front_cy - h)
        canvas.draw_polygon(
            [(cx - rx, cy), (cx, cy + ry), (front_cx, front_cy - h)],
            g_col,
        )
        if ridge_color is not None:
            canvas.draw_line(front_cx, front_cy - h, back_cx, back_cy - h, ridge_color)
            canvas.draw_line(cx - rx, cy, front_cx, front_cy - h, ridge_color)
            canvas.draw_line(cx, cy + ry, front_cx, front_cy - h, ridge_color)

    elif style == "gable_right":
        g_col = gable_color or right_color
        front_cx, front_cy = cx + rx // 2, cy + ry // 2
        back_cx, back_cy = cx - rx // 2, cy - ry // 2
        # Left sloped roof quad
        canvas.draw_polygon(
            [
                (back_cx, back_cy - h),
                (front_cx, front_cy - h),
                (cx, cy + ry),
                (cx - rx, cy),
            ],
            left_color,
        )
        # Right gable triangle
        canvas.draw_polygon(
            [(cx, cy + ry), (cx + rx, cy), (front_cx, front_cy - h)],
            g_col,
        )
        if ridge_color is not None:
            canvas.draw_line(back_cx, back_cy - h, front_cx, front_cy - h, ridge_color)
            canvas.draw_line(cx, cy + ry, front_cx, front_cy - h, ridge_color)
            canvas.draw_line(cx + rx, cy, front_cx, front_cy - h, ridge_color)
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
) -> None:
    """Draw a rectangle sheared to a 2:1 isometric 'left' or 'right' wall."""
    if w <= 0 or h <= 0:
        return
    slope = 1 if face == "left" else -1
    for dx in range(w):
        sy = y + (dx * slope) // 2
        canvas.draw_line(x + dx, sy, x + dx, sy + h - 1, color)

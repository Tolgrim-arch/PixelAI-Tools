"""2:1 Isometric projection primitives and auto-snapping 3D structure engine."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color


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


def draw_iso_wall_rect(
    canvas: Canvas,
    face: str,
    x: int | None = None,
    y: int | None = None,
    w: int = 4,
    h: int = 6,
    color: RGBA = (87, 56, 44, 255),
    border: RGBA | None = None,
    arch: bool = False,
    recessed: bool = True,
    role: str | None = None,
) -> None:
    """Draw a rectangle sheared to a 2:1 isometric 'left' or 'right' wall.

    Automatically snaps onto `canvas.last_iso_box` if (x, y) are omitted or if
    (x, y) would accidentally land on the box's top ceiling face.
    """
    _ = border
    if w <= 0 or h <= 0:
        return
    slope = 1 if face == "left" else -1

    if canvas.last_iso_box is not None:
        bcx, bcy, brx, bry, bh = canvas.last_iso_box
        is_door = (role == "door") or arch or (h >= max(5, (bh * 2) // 3))
        if x is None:
            if face == "left":
                x = bcx - brx + max(1, (brx - w) // 2)
            else:
                x = bcx + max(1, (brx - w) // 2)
        if face == "left":
            dx_wall = max(0, min(brx, x - (bcx - brx)))
            wall_top_y = bcy + int(round(bry * dx_wall / max(1, brx)))
        else:
            dx_wall = max(0, min(brx, x - bcx))
            wall_top_y = bcy + bry - int(round(bry * dx_wall / max(1, brx)))
        wall_bot_y = wall_top_y + bh - 1

        # Auto-snap if y was omitted OR if y was mistakenly placed on the ceiling (y <= wall_top_y + 1)
        if y is None or y <= wall_top_y + 1:
            if is_door:
                y = max(wall_top_y + 1, wall_bot_y - h + 1)
            else:
                y = wall_top_y + max(2, (bh - h) // 2)
    else:
        x = 0 if x is None else x
        y = 0 if y is None else y

    recess_col = darken(color, 0.68)
    sill_col = darken(color, 0.56)
    glint_col = (244, 250, 255, 255)
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
                if role == "window":
                    canvas.set_pixel(x + dx, y1, sill_col)
    if role == "window" and w >= 3 and h >= 3:
        if w >= 4 and h >= 4:
            mid_dx = w // 2
            msy = y + (mid_dx * slope) // 2
            canvas.draw_line(x + mid_dx, msy + 1, x + mid_dx, msy + h - 2, sill_col)
        gy0 = y + (1 * slope) // 2 + 1
        canvas.set_pixel(x + 1, gy0, glint_col)
        if w >= 4 and h >= 4:
            canvas.set_pixel(x + 2, y + (2 * slope) // 2 + 1, glint_col)


def _apply_eave_shadow(canvas: Canvas, cx: int, cy: int, rx: int, ry: int) -> None:
    """Darken 1px directly under the front-left and front-right roof eaves."""
    for dx in range(rx + 1):
        yl = cy + int(round(ry * dx / rx)) + 1
        yr = cy + ry - int(round(ry * dx / rx)) + 1
        cl = canvas.get_pixel(cx - rx + dx, yl)
        if cl[3] > 0:
            canvas.set_pixel(cx - rx + dx, yl, darken(cl, 0.72))
        cr = canvas.get_pixel(cx + dx, yr)
        if cr[3] > 0:
            canvas.set_pixel(cx + dx, yr, darken(cr, 0.72))


def draw_iso_roof(
    canvas: Canvas,
    cx: int | None = None,
    cy: int | None = None,
    rx: int | None = None,
    ry: int | None = None,
    h: int = 8,
    left_color: RGBA = (212, 96, 72, 255),
    right_color: RGBA = (168, 64, 52, 255),
    style: str = "pyramid",
    gable_color: RGBA | None = None,
    ridge_color: RGBA | None = None,
    eave_shadow: bool = True,
    bevel: bool = True,
    chimney: bool | dict[str, Any] = False,
    palette: dict[str, RGBA] | None = None,
) -> None:
    """Draw a lineless pitched isometric roof ('pyramid', 'gable_left', or 'gable_right').

    Automatically snaps flush onto `canvas.last_iso_box` if (cx, cy) are omitted
    or if `cy` would float above the box's top face.
    """
    _ = ridge_color
    if canvas.last_iso_box is not None:
        bcx, bcy, brx, bry, _ = canvas.last_iso_box
        if cx is None:
            cx = bcx
        if rx is None:
            rx = brx + 1
        if ry is None:
            ry = max(1, rx // 2)
        if cy is None or (abs(cx - bcx) <= 2 and cy < bcy):
            cy = bcy
    else:
        cx = 0 if cx is None else cx
        cy = 0 if cy is None else cy
        rx = 8 if rx is None else rx
        ry = max(1, rx // 2) if ry is None else ry

    if rx <= 0 or ry <= 0 or h <= 0:
        return
    apex_y = cy - h

    if eave_shadow:
        _apply_eave_shadow(canvas, cx, cy, rx, ry)

    if style == "pyramid":
        # Overdraw bottom ridge by 1px to guarantee zero gap with underlying box top
        canvas.draw_polygon(
            [(cx - rx, cy), (cx, cy + ry), (cx, apex_y)], left_color
        )
        canvas.draw_polygon(
            [(cx + rx, cy), (cx, cy + ry), (cx, apex_y)], right_color
        )
        # Subtle staggered shingle courses along both roof slopes
        l_sh = darken(left_color, 0.88)
        r_sh = darken(right_color, 0.88)
        for row in range(3, max(4, h + ry - 1), 3):
            frac = min(1.0, row / max(1, h + ry))
            lx_span = max(1, int(rx * frac) - 1)
            for sx in range(cx - lx_span, cx - 1, 4):
                sy_l = apex_y + row - int(round(ry * (cx - sx) / max(1, rx)))
                if sy_l > apex_y + 1:
                    canvas.draw_line(sx, sy_l, min(cx - 1, sx + 1), sy_l + 1, l_sh)
            for sx in range(cx + 2, cx + lx_span, 4):
                sy_r = apex_y + row - int(round(ry * (sx - cx) / max(1, rx)))
                if sy_r > apex_y + 1:
                    canvas.draw_line(sx, sy_r, min(cx + rx - 1, sx + 1), max(apex_y + 2, sy_r - 1), r_sh)
        if bevel:
            canvas.draw_line(cx, apex_y, cx, cy + ry, brighten(left_color, 1.12))

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
            hl = brighten(g_col, 1.14)
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
            hl = brighten(left_color, 1.14)
            canvas.draw_line(back_cx, back_cy - h, front_cx, front_cy - h, hl)
            canvas.draw_line(cx, cy + ry, front_cx, front_cy - h, hl)
    else:
        raise ValueError(f"Unknown iso_roof style: {style!r}")

    if chimney:
        pal = palette or {}
        c_spec = chimney if isinstance(chimney, dict) else {}
        c_rx = int(c_spec.get("rx", max(2, rx // 5)))
        c_ry = int(c_spec.get("ry", max(1, c_rx // 2)))
        c_h = int(c_spec.get("h", max(4, h // 2)))
        c_top = parse_color(c_spec.get("top", "stone_l"), pal) if "stone_l" in pal or "top" in c_spec else (176, 186, 201, 255)
        c_left = parse_color(c_spec.get("left", "stone"), pal) if "stone" in pal or "left" in c_spec else (130, 140, 158, 255)
        c_right = parse_color(c_spec.get("right", "stone_d"), pal) if "stone_d" in pal or "right" in c_spec else (92, 100, 117, 255)
        chim_cx = cx + max(2, rx // 3)
        chim_cy = cy - max(2, (h * 2) // 3)
        prev_box = canvas.last_iso_box
        draw_iso_box(
            canvas, chim_cx, chim_cy, c_rx, c_ry, c_h,
            c_top, c_left, c_right, bevel=bevel, ground_shadow=0,
        )
        canvas.last_iso_box = prev_box
        canvas.last_chimney = (chim_cx, chim_cy)


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
    door: dict[str, Any] | None = None,
    windows: list[dict[str, Any]] | None = None,
    roof: dict[str, Any] | None = None,
    palette: dict[str, RGBA] | None = None,
) -> None:
    """Draw a lineless 2:1 isometric 3D box with optional attached door, windows, and roof."""
    _ = edge_color  # Internal dark outlines are disabled by design
    if rx <= 0 or ry <= 0 or h < 0:
        return

    if ground_shadow > 0 and h > 0:
        for dx in range(rx + 1):
            y_base = cy + ry - int(round(ry * dx / rx)) + h - 1
            for s in range(1, ground_shadow + 1):
                gx, gy = cx + dx + s, y_base + (s // 2)
                existing = canvas.get_pixel(gx, gy)
                if existing[3] > 0:
                    canvas.set_pixel(gx, gy, darken(existing, 0.75))

    if h > 0:
        for dx in range(rx + 1):
            y_left = cy + int(round(ry * dx / rx))
            canvas.draw_line(cx - rx + dx, y_left, cx - rx + dx, y_left + h - 1, left_color)
            y_right = cy + ry - int(round(ry * dx / rx))
            canvas.draw_line(cx + dx, y_right, cx + dx, y_right + h - 1, right_color)

    draw_iso_tile(canvas, cx, cy, rx, ry, top_color, border=None)

    if bevel and h > 0:
        hl_top = brighten(top_color, 1.12)
        hl_left = brighten(left_color, 1.14)
        for dx in range(rx + 1):
            yl = cy + int(round(ry * dx / rx))
            yr = cy + ry - int(round(ry * dx / rx))
            canvas.set_pixel(cx - rx + dx, yl, hl_top)
            canvas.set_pixel(cx + dx, yr, hl_top)
        canvas.draw_line(cx, cy + ry + 1, cx, cy + ry + h - 1, hl_left)

    canvas.last_iso_box = (cx, cy, rx, ry, h)
    pal = palette or {}

    if door:
        draw_iso_wall_rect(
            canvas,
            face=door.get("face", "left"),
            x=door.get("x"),
            y=door.get("y"),
            w=int(door.get("w", max(3, rx // 3))),
            h=int(door.get("h", max(4, h // 2))),
            color=parse_color(door.get("color", "wood_d"), pal),
            arch=bool(door.get("arch", True)),
            recessed=bool(door.get("recessed", True)),
            role="door",
        )

    if windows:
        for win in windows:
            draw_iso_wall_rect(
                canvas,
                face=win.get("face", "right"),
                x=win.get("x"),
                y=win.get("y"),
                w=int(win.get("w", max(3, rx // 4))),
                h=int(win.get("h", max(3, h // 3))),
                color=parse_color(win.get("color", "water_l"), pal),
                arch=bool(win.get("arch", False)),
                recessed=bool(win.get("recessed", True)),
                role="window",
            )

    if roof:
        r_overhang = int(roof.get("overhang", 1))
        r_rx = int(roof.get("rx", rx + r_overhang))
        r_ry = int(roof.get("ry", max(1, r_rx // 2)))
        r_h = int(roof.get("h", max(6, int(rx * 0.75))))
        gable = parse_color(roof["gable"], pal) if "gable" in roof else None
        draw_iso_roof(
            canvas,
            cx=cx,
            cy=cy,
            rx=r_rx,
            ry=r_ry,
            h=r_h,
            left_color=parse_color(roof.get("left", "roof_l"), pal),
            right_color=parse_color(roof.get("right", "roof_d"), pal),
            style=roof.get("style", "pyramid"),
            gable_color=gable,
            eave_shadow=bool(roof.get("eave_shadow", True)),
            bevel=bool(roof.get("bevel", bevel)),
            chimney=roof.get("chimney", False),
            palette=pal,
        )


def draw_iso_structure(
    canvas: Canvas,
    origin_x: int,
    origin_y: int,
    items: list[dict[str, Any]],
    palette: dict[str, RGBA],
    step_x: int | None = None,
    step_y: int | None = None,
    default_bevel: bool = True,
    default_ground_shadow: int = 2,
    use_zbuffer: bool = True,
) -> None:
    """Sort and render 3D lineless isometric boxes/roofs with automatic roof & floor alignment."""
    _ = use_zbuffer
    sorted_items = sorted(
        items,
        key=lambda it: (
            float(it.get("gx", 0)) + float(it.get("gy", 0)),
            float(it.get("gz", 0)),
            1 if it.get("type", "box") == "roof" else 0,
        ),
    )

    # Determine primary ground box at (0, 0) for floor alignment and tile step size
    base_rx = 8
    base_ry = 4
    base_h = 0
    for it in sorted_items:
        if it.get("type", "box") == "box" and int(it.get("gx", 0)) == 0 and int(it.get("gy", 0)) == 0 and int(it.get("gz", 0)) == 0:
            base_rx = int(it["rx"])
            base_ry = int(it.get("ry", max(1, base_rx // 2)))
            base_h = int(it["h"])
            break

    # Track rendered boxes by (gx, gy) -> (cx, top_cy, rx, ry, h) so roofs/chimneys snap cleanly
    box_tops: dict[tuple[int, int], tuple[int, int, int, int, int]] = {}
    roof_tops: dict[tuple[int, int], tuple[int, int, int, int, int]] = {}

    for it in sorted_items:
        gx = int(it.get("gx", 0))
        gy = int(it.get("gy", 0))
        gz = int(it.get("gz", 0))
        rx = int(it["rx"])
        ry = int(it.get("ry", max(1, rx // 2)))
        h = int(it["h"])
        kind = it.get("type", "box")
        bevel = bool(it.get("bevel", default_bevel))

        # If small grid coordinates (|gx|, |gy| <= 2) are used without explicit step_x/step_y,
        # step by half the combined radii so adjacent wings sit flush against the main building!
        if step_x is None and step_y is None and (gx != 0 or gy != 0) and abs(gx) <= 2 and abs(gy) <= 2:
            eff_step_x = max(2, (base_rx + rx) // 2)
            eff_step_y = max(1, (base_ry + ry) // 2)
        else:
            eff_step_x = 2 if step_x is None else step_x
            eff_step_y = 1 if step_y is None else step_y

        cx = origin_x + (gx - gy) * eff_step_x
        cy = origin_y + (gx + gy) * eff_step_y - gz

        if kind == "box":
            # Align ground floor (gz == 0) across boxes of different heights
            if gz == 0 and base_h > 0 and h != base_h:
                cy += (base_h - h)
            # If this is a small chimney box placed above a roof at (gx, gy), snap it onto the roof slope!
            if (gx, gy) in roof_tops and rx <= max(4, base_rx // 3):
                rcx, rcy, rrx, _, rh = roof_tops[(gx, gy)]
                cx = rcx + max(2, rrx // 3)
                cy = rcy - max(2, (rh * 2) // 3)
                canvas.last_chimney = (cx, cy)
            elif (gx, gy) in box_tops and gz > 0:
                # Stacking a box on top of a lower box at (gx, gy): ensure its bottom touches the lower box's top
                _, prev_top_cy, _, _, _ = box_tops[(gx, gy)]
                if cy < prev_top_cy - h:
                    cy = prev_top_cy - h

            g_shadow = int(it.get("ground_shadow", default_ground_shadow if gz == 0 else 0))
            wins = it.get("windows") or ([it["window"]] if "window" in it else None)
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
                door=it.get("door"),
                windows=wins,
                roof=it.get("roof"),
                palette=palette,
            )
            if (gx, gy) not in box_tops or rx > max(4, base_rx // 3):
                box_tops[(gx, gy)] = (cx, cy, rx, ry, h)
        elif kind == "roof":
            # Always snap roof base onto the top face of the box at (gx, gy) so it never floats!
            if (gx, gy) in box_tops:
                bcx, bcy, brx, _, _ = box_tops[(gx, gy)]
                cx = bcx
                cy = bcy
                if rx <= brx:
                    rx = rx + int(it.get("overhang", 1))
                    ry = max(1, rx // 2)
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
                chimney=it.get("chimney", False),
                palette=palette,
            )
            roof_tops[(gx, gy)] = (cx, cy, rx, ry, h)
        else:
            raise ValueError(f"Unknown iso_structure item type: {kind!r}")

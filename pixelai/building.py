"""Top-down 3/4 cozy building generator (farmhouses, cottages, barns)."""

from math import hypot
from random import Random
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color


def _resolve(name: str, palette: dict[str, RGBA], fallback: RGBA) -> RGBA:
    if name in palette:
        return palette[name]
    try:
        return parse_color(name, palette)
    except ValueError:
        return fallback


def _shingle_slope(canvas, corners, color, seed, tile_width):
    """Lay staggered, unequal shingles in the projected plane of a roof slope."""
    ridge_l, ridge_r, eave_r, eave_l = corners
    width = max(1, round(hypot(eave_r[0] - eave_l[0], eave_r[1] - eave_l[1])))
    height = max(1, round(hypot(eave_l[0] - ridge_l[0], eave_l[1] - ridge_l[1])))
    rng = Random(seed)
    colors = (darken(color, .94), color, color, brighten(color, 1.02))

    def point(x, y):
        u, v = x / width, y / height
        return tuple(round((a + (b - a) * u) * (1 - v) + (d + (c - d) * u) * v)
                     for a, b, c, d in zip(ridge_l, ridge_r, eave_r, eave_l))

    canvas.draw_polygon(corners, color)
    row_h = max(3, round(tile_width * .62))
    for i, top in enumerate(range(0, height, row_h)):
        bottom = min(top + row_h, height)
        left = -rng.randint(0, max(1, tile_width // 3)) - (i % 2) * (tile_width // 2)
        while left < width:
            right = left + rng.randint(max(3, tile_width * 2 // 3), max(4, tile_width * 4 // 3))
            if right > 0:
                start, end = max(0, left), min(width, right)
                face = rng.choice(colors)
                bevel = 1 if end - start > 4 else 0
                bottom_l, bottom_r = point(start + bevel, bottom), point(end - bevel, bottom)
                canvas.draw_polygon([point(start, top), point(end, top), point(end, max(top, bottom - 1)), bottom_r,
                                     bottom_l, point(start, max(top, bottom - 1))], face)
                if bottom - top >= 3:
                    canvas.draw_line(*bottom_l, *bottom_r, darken(face, .87))
                if end - start > tile_width and rng.random() < .42 and bottom - top >= 4:
                    canvas.draw_line(*point(start + 2, top + 1), *point(end - 2, top + 1), brighten(face, 1.06))
            left = right


def draw_building(
    canvas: Canvas,
    palette: dict[str, RGBA],
    op: dict[str, Any],
    frame_idx: int = 0,
    total_frames: int = 1,
) -> None:
    """Draw a top-down 3/4 cozy building (farmhouse, cottage, or barn) with lineless bevels."""
    if "architecture" in op:
        from pixelai.architecture import draw_architecture
        draw_architecture(canvas, palette, op)
        return
    if "massing_only" in op:
        raise ValueError("massing_only requires architecture mode")
    bw = int(op.get("w", max(32, int(canvas.width * 0.78))))
    bh = int(op.get("h", max(32, int(canvas.height * 0.78))))
    bx = int(op.get("x", (canvas.width - bw) // 2))
    by = int(op.get("y", max(8, (canvas.height - bh) // 2 + 4)))
    style = str(op.get("roof_style", op.get("variant", "gable"))).lower()
    seed = int(op.get("seed", 42))

    # Resolve cozy palette colors with safe fallbacks
    c_shadow = _resolve(str(op.get("shadow_color", "shadow")), palette, (51, 41, 58, 255))
    c_wall = _resolve(str(op.get("wall_color", "roof" if style == "barn" else "cream")), palette, (250, 240, 215, 255))
    c_roof = _resolve(str(op.get("roof_color", "roof")), palette, (194, 75, 56, 255))
    c_roof_l = _resolve("roof_l", palette, brighten(c_roof, 1.18)) if "roof_color" not in op else brighten(c_roof, 1.18)
    c_roof_d = _resolve("roof_d", palette, darken(c_roof, 0.78)) if "roof_color" not in op else darken(c_roof, 0.78)
    c_wood = _resolve(str(op.get("trim_color", "wood")), palette, (143, 92, 60, 255))
    c_wood_l = _resolve("wood_l", palette, brighten(c_wood, 1.18)) if "trim_color" not in op else brighten(c_wood, 1.18)
    c_wood_d = _resolve("wood_d", palette, darken(c_wood, 0.75)) if "trim_color" not in op else darken(c_wood, 0.75)
    c_stone = _resolve(str(op.get("foundation_color", "stone")), palette, (130, 140, 158, 255))
    c_stone_l = _resolve("stone_l", palette, brighten(c_stone, 1.2)) if "foundation_color" not in op else brighten(c_stone, 1.2)
    c_stone_d = _resolve("stone_d", palette, darken(c_stone, 0.75)) if "foundation_color" not in op else darken(c_stone, 0.75)
    c_water = _resolve("water", palette, (74, 156, 194, 255))
    c_water_l = _resolve("water_l", palette, brighten(c_water, 1.25))
    c_grass = _resolve("grass", palette, (92, 168, 76, 255))
    c_grass_d = _resolve("grass_d", palette, darken(c_grass, 0.78))
    c_wheat = _resolve("wheat", palette, (242, 191, 82, 255))
    c_wheat_l = _resolve("wheat_l", palette, brighten(c_wheat, 1.18))
    c_cream = _resolve("cream", palette, (250, 240, 215, 255))

    overhang = max(2, bw // 18)
    wall_x = bx + overhang
    depth = min(bw // 3, max(5, int(op.get("depth", round(bw * .22)))))
    return_rise = max(4, round(depth * .61))
    wall_w = bw - overhang * 2 - depth
    wall_r = wall_x + wall_w - 1
    roof_h = int(op.get("roof_h", max(14, int(bh * 0.46))))
    found_h = int(op.get("foundation_h", max(4, int(bh * 0.10))))
    wall_y = by + roof_h
    wall_h = max(10, bh - roof_h - found_h)
    found_y = wall_y + wall_h
    found_x = wall_x - max(1, overhang // 2)
    found_w = wall_w + max(1, overhang // 2) * 2
    found_r = found_x + found_w - 1

    # 1. Ground shadow (marked as shadow so external outline draws cleanly over it)
    if op.get("ground_shadow", True):
        prev_sh, prev_no = canvas.mark_shadow, canvas.mark_no_outline
        canvas.mark_shadow = True
        canvas.mark_no_outline = True
        try:
            opacity = float(op.get("shadow_opacity", 0.22))
            if not 0.0 <= opacity <= 1.0:
                raise ValueError("shadow_opacity must be between 0 and 1")
            shadow = (*c_shadow[:3], round(c_shadow[3] * opacity))
            # A building casts a straight-edged footprint, never a tree-like oval.
            dx = int(op.get("shadow_dx", max(3, bw // 10)))
            dy = int(op.get("shadow_dy", max(2, bh // 16)))
            foot_y = found_y + found_h - 1
            canvas.draw_polygon(
                [(found_x, found_y), (found_r + depth, found_y - return_rise),
                 (found_r + depth + dx, foot_y + dy),
                 (found_x + dx, foot_y + dy)],
                shadow, filled=True,
            )
        finally:
            canvas.mark_shadow, canvas.mark_no_outline = prev_sh, prev_no

    # The side uses the same floor and eave lines as the front, projected back into depth.
    side_x = wall_r + depth
    side_wall = darken(c_wall, .79)
    canvas.draw_polygon([(wall_r, wall_y), (side_x, wall_y - return_rise),
                         (side_x, found_y - return_rise), (wall_r, found_y)], side_wall)
    side_eave = max(2, roof_h // 10)
    canvas.draw_polygon([(wall_r, wall_y), (side_x, wall_y - return_rise),
                         (side_x, wall_y - return_rise + side_eave), (wall_r, wall_y + side_eave)],
                        darken(c_wall, .68))
    canvas.draw_polygon([(found_r, found_y), (found_r + depth, found_y - return_rise),
                         (found_r + depth, found_y + found_h - return_rise - 1),
                         (found_r, found_y + found_h - 1)], c_stone_d)
    canvas.draw_line(found_r, found_y, found_r + depth, found_y - return_rise, c_stone)
    if op.get("windows", style != "barn") and depth >= 12 and wall_h >= 16:
        side_win_x = wall_r + depth // 4
        side_win_y = wall_y + max(5, wall_h // 3)
        side_win_w, side_win_h = max(4, depth // 2), max(5, wall_h * 2 // 5)
        lean = max(2, round(side_win_w * return_rise / depth))
        canvas.draw_polygon([(side_win_x, side_win_y), (side_win_x + side_win_w, side_win_y - lean),
                             (side_win_x + side_win_w, side_win_y + side_win_h - lean),
                             (side_win_x, side_win_y + side_win_h)], c_wood_d)
        canvas.draw_polygon([(side_win_x + 1, side_win_y + 1), (side_win_x + side_win_w - 1, side_win_y - lean + 2),
                             (side_win_x + side_win_w - 1, side_win_y + side_win_h - lean - 1),
                             (side_win_x + 1, side_win_y + side_win_h - 1)], darken(c_water, .82))
        canvas.draw_line(side_win_x + 1, side_win_y + side_win_h // 2,
                         side_win_x + side_win_w - 1, side_win_y + side_win_h // 2 - lean + 1, c_wood)
        canvas.draw_line(side_win_x - 1, side_win_y + side_win_h + 1,
                         side_win_x + side_win_w + 1, side_win_y + side_win_h - lean + 1, c_wood_l)

    # 2. Stone Foundation
    canvas.draw_rect(found_x, found_y, found_w, found_h, c_stone, filled=True)
    canvas.draw_rect(found_x, found_y, found_w, max(1, found_h // 5), c_stone_l, filled=True)
    canvas.draw_rect(found_x, found_y + found_h - max(1, found_h // 4), found_w, max(1, found_h // 4), c_stone_d, filled=True)
    canvas.scatter(
        found_x + 1,
        found_y + max(1, found_h // 5),
        found_w - 2,
        max(1, found_h - max(2, found_h // 2)),
        c_stone_d,
        density=0.55,
        seed=seed + 11,
        target_color=c_stone,
        pattern="cobble" if found_h >= 8 else "brick",
    )

    # 4. Main Facade Wall + Eave Shadow + Timber Framing
    canvas.draw_rect(wall_x, wall_y, wall_w, wall_h, c_wall, filled=True)
    eave_sh_h = max(2, wall_h // 9)
    canvas.draw_rect(wall_x, wall_y, wall_w, eave_sh_h, darken(c_wall, 0.76), filled=True)

    post_w = max(2, wall_w // 18)
    if op.get("timber_frame", True):
        # Left & right corner timber posts
        canvas.draw_rect(wall_x, wall_y, post_w, wall_h, c_wood, filled=True)
        canvas.draw_rect(wall_x, wall_y, max(1, post_w // 2), wall_h, c_wood_l, filled=True)
        canvas.draw_rect(wall_x + wall_w - post_w, wall_y, post_w, wall_h, c_wood_d, filled=True)
        # Horizontal mid-wall timber beam
        beam_y = wall_y + wall_h // 2 - 1
        beam_h = max(2, wall_h // 14)
        canvas.draw_rect(wall_x + post_w, beam_y, wall_w - post_w * 2, beam_h, c_wood, filled=True)
        canvas.draw_rect(wall_x + post_w, beam_y, wall_w - post_w * 2, 1, c_wood_l, filled=True)
    elif style == "barn":
        board_step = max(5, wall_w // 9)
        for offset in range(board_step, wall_w, board_step):
            face = brighten(c_wall, 1.0) if offset % (board_step * 3) == 0 else darken(c_wall, .96)
            canvas.draw_rect(wall_x + offset, wall_y + eave_sh_h, min(wall_w - offset, max(1, board_step // 4)),
                             wall_h - eave_sh_h, face)

    # 5. Door & Step
    if op.get("door", True):
        door_w = max(8, int(wall_w * (0.34 if style == "barn" else 0.25)))
        door_h = max(10, int(wall_h * 0.80))
        door_x = wall_x + (wall_w - door_w) // 2 if style == "barn" else wall_x + max(post_w + 3, int(wall_w * 0.16))
        door_y = found_y - door_h
        frame_t = max(1, door_w // 10)

        # Outer frame + recessed inner plank surface
        canvas.draw_rect(door_x, door_y, door_w, door_h, c_wood_d, filled=True)
        inner_x = door_x + frame_t
        inner_y = door_y + frame_t
        inner_w = max(2, door_w - frame_t * 2)
        inner_h = max(2, door_h - frame_t)
        canvas.draw_rect(inner_x, inner_y, inner_w, inner_h, c_wood, filled=True)
        # Top recessed shadow lip inside door frame
        canvas.draw_rect(inner_x, inner_y, inner_w, max(1, frame_t), darken(c_wood_d, 0.82), filled=True)
        # Left highlight plank
        canvas.draw_rect(inner_x + 1, inner_y + max(1, frame_t), max(1, inner_w // 5), inner_h - max(1, frame_t), c_wood_l, filled=True)
        # Vertical plank seams
        for px in range(inner_x + max(3, inner_w // 3), inner_x + inner_w - 2, max(3, inner_w // 3)):
            canvas.draw_line(px, inner_y + 1, px, inner_y + inner_h - 1, c_wood_d)

        if style == "barn":
            for left, right in ((inner_x + 1, inner_x + inner_w - 2), (inner_x + inner_w - 2, inner_x + 1)):
                canvas.draw_polygon([(left, inner_y + 1), (left + 1, inner_y + 1),
                                     (right + 1, inner_y + inner_h - 2), (right, inner_y + inner_h - 2)], c_wood_l)
            canvas.draw_rect(inner_x + inner_w // 2, inner_y + 1, 1, inner_h - 1, c_wood_d)
        else:
            # Door handle
            hx = inner_x + inner_w - max(2, inner_w // 5)
            hy = door_y + door_h // 2
            canvas.draw_rect(hx, hy, max(1, frame_t), max(2, frame_t + 1), c_wheat, filled=True)

        # Stone doorstep aligned under door
        step_x = door_x - frame_t
        step_w = door_w + frame_t * 2
        canvas.draw_rect(step_x, found_y, step_w, found_h, c_stone_l, filled=True)
        canvas.draw_rect(step_x, found_y + found_h // 2, step_w, 1, c_stone_d, filled=True)
        canvas.draw_rect(step_x, found_y + found_h - max(1, found_h // 4), step_w, max(1, found_h // 4), c_stone, filled=True)

    # 6. Window + Shutters + Flowerbox
    if op.get("windows", style != "barn"):
        win_w = max(8, int(wall_w * 0.22))
        win_h = max(7, int(wall_h * 0.44))
        win_x = wall_x + wall_w - post_w - win_w - max(4, wall_w // 10)
        win_y = wall_y + max(eave_sh_h + 2, int(wall_h * 0.22))
        frame_t = max(1, win_w // 9)

        # Wooden shutters on left and right
        shutter_w = max(2, win_w // 6)
        canvas.draw_rect(win_x - shutter_w, win_y + 1, shutter_w, win_h - 2, c_wood, filled=True)
        canvas.draw_rect(win_x - shutter_w, win_y + 1, 1, win_h - 2, c_wood_l, filled=True)
        canvas.draw_rect(win_x + win_w, win_y + 1, shutter_w, win_h - 2, c_wood_d, filled=True)

        # Window frame & glass
        canvas.draw_rect(win_x, win_y, win_w, win_h, c_wood_d, filled=True)
        gx, gy = win_x + frame_t, win_y + frame_t
        gw, gh = max(2, win_w - frame_t * 2), max(2, win_h - frame_t * 2)
        canvas.draw_rect(gx, gy, gw, gh, c_water, filled=True)
        canvas.draw_rect(gx, gy, gw, 1, darken(c_water, 0.78), filled=True)
        # Specular glass reflection lines
        canvas.draw_line(gx + 1, gy + gh - 2, gx + gw - 2, gy + 1, c_water_l)
        if gw >= 8:
            canvas.draw_line(gx + 3, gy + gh - 2, gx + gw - 2, gy + 3, c_water_l)
        # Window mullions (crossbars)
        canvas.draw_rect(gx + gw // 2 - max(0, frame_t // 2), gy, max(1, frame_t), gh, c_wood, filled=True)
        canvas.draw_rect(gx, gy + gh // 2 - max(0, frame_t // 2), gw, max(1, frame_t), c_wood, filled=True)

        # Cozy flower box underneath window
        box_h = max(3, wall_h // 8)
        box_y = win_y + win_h
        canvas.draw_rect(win_x - 1, box_y, win_w + 2, box_h, c_wood, filled=True)
        canvas.draw_rect(win_x - 1, box_y + box_h - 1, win_w + 2, 1, c_wood_d, filled=True)
        fol_h = max(2, box_h // 2 + 1)
        canvas.draw_rect(win_x, box_y, win_w, 1, c_grass_d)
        for offset, height, blossom in ((win_w // 5, fol_h, c_roof_l), (win_w // 2, fol_h + 1, c_wheat_l),
                                        (win_w * 4 // 5, fol_h - 1, c_cream)):
            fx = win_x + offset
            radius = min(offset, win_w - offset - 1, max(1, win_w // 6))
            canvas.draw_polygon([(fx - radius, box_y), (fx - radius + 1, box_y - height // 2),
                                 (fx, box_y - height), (fx + radius - 1, box_y - height // 2),
                                 (fx + radius, box_y)], c_grass)
            canvas.set_pixel(fx, box_y - height, blossom)
            if radius >= 2:
                canvas.set_pixel(fx + 1, box_y - height + 1, blossom)

    # 7. Front roof pitch and the visible gable end above the side wall.
    roof_w = bw - depth
    ridge_shift = depth if style in ("pitched", "shed") else (depth + 1) // 2
    front_l = (bx, wall_y - 1)
    front_r = (bx + roof_w - 1, wall_y - 1)
    back_r = (bx + bw - 1, wall_y - 1 - return_rise)
    ridge_l = (front_l[0] + ridge_shift, by)
    ridge_r = (front_r[0] + ridge_shift, by)
    eave_y = wall_y - 1
    fascia_h = max(2, roof_h // 11)
    tile_width = max(5, bw // 11)
    if style == "barn":
        break_shift = max(1, ridge_shift // 3)
        break_y = by + roof_h * 45 // 100
        break_l = (front_l[0] + break_shift, break_y)
        break_r = (front_r[0] + break_shift, break_y)
        rear_break = (back_r[0] - break_shift, break_y - return_rise // 2)
        canvas.draw_polygon([front_r, break_r, ridge_r, rear_break, back_r], side_wall)
        _shingle_slope(canvas, [ridge_l, ridge_r, break_r, break_l], c_roof_l, seed, tile_width)
        _shingle_slope(canvas, [break_l, break_r, front_r, front_l], c_roof, seed + 1, tile_width)
        right_rake = [front_r, break_r, ridge_r, rear_break, back_r]
    else:
        canvas.draw_polygon([front_r, ridge_r, back_r], side_wall)
        _shingle_slope(canvas, [ridge_l, ridge_r, front_r, front_l], c_roof, seed, tile_width)
        right_rake = [front_r, ridge_r, back_r]
    # A beam lip on the rake casts shade down the side gable and along the back eave.
    for start, end in zip(right_rake, right_rake[1:]):
        canvas.draw_polygon([start, end, (end[0], end[1] + fascia_h),
                             (start[0], start[1] + fascia_h)], c_wood_d)
        canvas.draw_line(*start, *end, c_roof_d)
    if style in ("gable", "farmhouse", "barn") and depth >= 17 and roof_h >= 26:
        vx = ridge_r[0] - 1
        vy = by + roof_h * 48 // 100
        vw = max(4, depth // 4)
        vh = max(5, roof_h // 5)
        canvas.draw_polygon([(vx, vy), (vx + vw, vy - 3), (vx + vw, vy + vh - 3), (vx, vy + vh)], c_wood)
        for slat in range(vy + 2, vy + vh - 1, 2):
            canvas.draw_line(vx + 1, slat, vx + vw - 1, slat - 2, darken(c_wall, .59))
    canvas.draw_line(*ridge_l, *ridge_r, c_roof_l)
    canvas.draw_line(*front_l, *ridge_l, c_roof_l)
    canvas.draw_rect(bx, eave_y - fascia_h + 1, roof_w, fascia_h, c_wood)
    canvas.draw_rect(bx, eave_y - fascia_h + 1, roof_w, 1, c_wood_l)
    canvas.draw_rect(bx, eave_y, roof_w, 1, c_wood_d)

    # 8. Cross-gable: the short ridge and both roof returns meet the main pitch uphill.
    if op.get("dormer", style in ("gable", "farmhouse", "barn")) and roof_w >= 27 and roof_h >= 14:
        g_half_w = max(7, roof_w * (22 if style == "barn" else 20) // 100)
        rng = Random(seed + 79)
        cx_mid = bx + (roof_w // 2 if style == "barn" else roof_w * 41 // 100 + rng.randint(-2, 2))
        g_base_y = eave_y + 1
        g_peak_y = eave_y - max(9, roof_h * (55 if style == "barn" else 61) // 100)
        left = (cx_mid - g_half_w, g_base_y)
        peak = (cx_mid, g_peak_y)
        right = (cx_mid + g_half_w, g_base_y)
        uphill = max(5, (g_peak_y - by) * 3 // 4)
        skew = max(2, ridge_shift * uphill // max(1, roof_h))
        rear_peak = (cx_mid + skew, g_peak_y - uphill)
        left_valley = (cx_mid - g_half_w + skew + max(1, g_half_w // 5), g_base_y - uphill)
        right_valley = (cx_mid + g_half_w + skew, g_base_y - uphill - max(2, roof_h // 10))
        canvas.draw_polygon([right, right_valley, (right_valley[0] + 4, right_valley[1] + 4),
                             (right[0] + 4, right[1] - 2)], c_roof_d)
        _shingle_slope(canvas, [rear_peak, peak, left, left_valley], c_roof_d, seed + 61, max(4, tile_width - 1))
        _shingle_slope(canvas, [peak, rear_peak, right_valley, right], brighten(c_roof, 1.09), seed + 63,
                       max(4, tile_width - 1))
        canvas.draw_polygon([left, peak, right], c_wall)
        canvas.draw_line(*peak, *rear_peak, c_roof_l)
        for start, end, trim in ((peak, left, c_wood_l), (peak, right, c_wood)):
            canvas.draw_polygon([start, end, (end[0], end[1] + fascia_h),
                                 (start[0], start[1] + fascia_h)], trim)
        canvas.draw_rect(left[0] + 1, g_base_y, g_half_w * 2 - 1, 1, c_wood)

        # Attic round window or barn hayloft opening inside the gable.
        attic_r = max(2, min(g_half_w // 3, (g_base_y - g_peak_y) // 5))
        attic_cy = g_peak_y + (g_base_y - g_peak_y) * 7 // 10 - 1
        if style == "barn":
            lw = attic_r * 2
            lh = attic_r * 2
            canvas.draw_rect(cx_mid - attic_r, attic_cy - attic_r, lw, lh, c_wood_d, filled=True)
            canvas.draw_rect(cx_mid - attic_r + 1, attic_cy - attic_r + 1, lw - 2, lh - 2, c_shadow, filled=True)
        else:
            canvas.draw_circle(cx_mid, attic_cy, attic_r + 1, c_wood_d, filled=True)
            canvas.draw_circle(cx_mid, attic_cy, attic_r, c_water, filled=True)
            canvas.draw_line(cx_mid - attic_r + 1, attic_cy + 1, cx_mid + 1, attic_cy - attic_r + 1, c_water_l)
            canvas.draw_line(cx_mid, attic_cy - attic_r, cx_mid, attic_cy + attic_r, c_wood)
            canvas.draw_line(cx_mid - attic_r, attic_cy, cx_mid + attic_r, attic_cy, c_wood)

    # 9. Chimney emerging from right roof slope + Smoke
    if op.get("chimney", style != "barn"):
        cw = max(6, bw // 8)
        ch = max(10, roof_h // 3 + 5)
        cx = wall_x + wall_w - cw - max(6, wall_w // 6)
        cheek = max(3, cw // 3)
        lift = max(2, cheek // 2)
        min_cy = max(9, cw // 2 + 4) if op.get("smoke", True) else lift + 1
        cy = max(min_cy, by - max(4, ch // 4))
        cr = cx + cw - 1
        canvas.draw_polygon([(cx - 2, cy + ch - 1), (cr + cheek + 3, cy + ch - lift - 1),
                             (cr + cheek + 5, cy + ch), (cx, cy + ch + 1)], c_roof_d)
        canvas.draw_rect(cx, cy, cw, ch, c_stone)
        canvas.draw_rect(cx, cy, 1, ch, c_stone_l)
        canvas.draw_polygon([(cr, cy), (cr + cheek, cy - lift), (cr + cheek, cy + ch - lift - 1),
                             (cr, cy + ch - 1)], c_stone_d)
        for course in range(4, ch - 2, max(3, cw // 3)):
            mortar = cy + course
            canvas.draw_line(cx + 1, mortar, cr - 1, mortar, darken(c_stone, .88))
            joint = cx + cw * (1 if course % 2 else 2) // 3
            canvas.draw_line(joint, mortar, joint, mortar - 2, darken(c_stone, .9))
        cap_h = max(2, ch // 6)
        canvas.draw_rect(cx - 1, cy, cw + 2, cap_h, c_stone_l)
        canvas.draw_polygon([(cr + 1, cy), (cr + cheek + 1, cy - lift),
                             (cr + cheek + 1, cy - lift + cap_h), (cr + 1, cy + cap_h)], darken(c_stone, .88))
        canvas.draw_polygon([(cx - 1, cy), (cx + cheek - 1, cy - lift),
                             (cr + cheek + 1, cy - lift), (cr + 1, cy)], c_stone_l)
        canvas.draw_line(cx + cheek, cy - 1, cr - 1, cy - 1, c_stone_d)
        canvas.last_chimney = (cx + cw // 2, cy - lift)

        if op.get("smoke", True):
            prev_no = canvas.mark_no_outline
            canvas.mark_no_outline = True
            smoke_cx = cx + cw // 2
            phase = frame_idx % max(1, total_frames)
            r1 = max(2, cw // 4)
            r2 = max(1, cw // 5)
            y1 = max(r1 + 1, cy - r1 - 2)
            y2 = max(r2 + 1, y1 - r1 - r2)
            canvas.draw_circle(smoke_cx + (phase % 2), y1, r1, c_cream, filled=True)
            canvas.draw_circle(smoke_cx + 3 + ((phase + 1) % 2), y2, r2, c_cream, filled=True)
            canvas.mark_no_outline = prev_no

    canvas.attachments.append({
        "type": "building",
        "name": str(op.get("name", f"{style}_building")),
        "origin": [found_x + found_w // 2, found_y + found_h - 1],
        "y_sort": [found_x + found_w // 2, found_y + found_h - 1],
        "collision": {
            "shape": "polygon",
            "points": [
                [found_x, found_y],
                [found_r, found_y],
                [found_r + depth, found_y - return_rise],
                [found_r + depth, found_y + found_h - return_rise - 1],
                [found_x, found_y + found_h - 1],
            ],
        },
        "entrance": [door_x + door_w // 2, found_y + found_h - 1],
    })

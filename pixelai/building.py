"""Top-down 3/4 cozy building generator (farmhouses, cottages, barns)."""

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


def draw_building(
    canvas: Canvas,
    palette: dict[str, RGBA],
    op: dict[str, Any],
    frame_idx: int = 0,
    total_frames: int = 1,
) -> None:
    """Draw a top-down 3/4 cozy building (farmhouse, cottage, or barn) with lineless bevels."""
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
    wall_w = bw - overhang * 2
    roof_h = int(op.get("roof_h", max(14, int(bh * 0.46))))
    found_h = int(op.get("foundation_h", max(4, int(bh * 0.10))))
    wall_y = by + roof_h
    wall_h = max(10, bh - roof_h - found_h)
    found_y = wall_y + wall_h
    found_x = wall_x - max(1, overhang // 2)
    found_w = wall_w + max(1, overhang // 2) * 2

    # 1. Ground shadow (marked as shadow so external outline draws cleanly over it)
    if op.get("ground_shadow", True):
        prev_sh, prev_no = canvas.mark_shadow, canvas.mark_no_outline
        canvas.mark_shadow = True
        canvas.mark_no_outline = True
        sh_rx = bw // 2 + max(2, overhang)
        sh_ry = max(3, bh // 14)
        canvas.draw_ellipse(bx + bw // 2, found_y + found_h - 1, sh_rx, sh_ry, c_shadow, filled=True)
        canvas.mark_shadow, canvas.mark_no_outline = prev_sh, prev_no

    # 2.Stone Foundation
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
            canvas.draw_line(inner_x + 1, inner_y + 1, inner_x + inner_w - 2, inner_y + inner_h - 2, c_cream)
            canvas.draw_line(inner_x + inner_w - 2, inner_y + 1, inner_x + 1, inner_y + inner_h - 2, c_cream)
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
        canvas.draw_rect(win_x, box_y - fol_h + 1, win_w, fol_h, c_grass, filled=True)
        canvas.draw_rect(win_x, box_y, win_w, 1, c_grass_d, filled=True)
        for fx_off, fcol in ((2, c_roof_l), (win_w // 2, c_wheat_l), (win_w - 3, c_cream)):
            if 1 <= fx_off < win_w - 1:
                canvas.set_pixel(win_x + fx_off, box_y - fol_h + 1, fcol)

    # 7. Pitched Roof + Shingle Texture + Eave Trim
    neck = max(6, bw // 7)
    top_l = bx + neck
    top_r = bx + bw - 1 - neck
    bot_l = bx
    bot_r = bx + bw - 1
    eave_y = wall_y - 1

    canvas.draw_polygon([(top_l, by), (top_r, by), (bot_r, eave_y), (bot_l, eave_y)], c_roof, filled=True)
    # Right-side directional roof slope shadow
    sh_top_l = top_r - max(4, (top_r - top_l) // 4)
    sh_bot_l = bot_r - max(6, bw // 5)
    canvas.draw_polygon([(sh_top_l, by), (top_r, by), (bot_r, eave_y), (sh_bot_l, eave_y)], c_roof_d, filled=True)
    # Left-side specular slope highlight
    canvas.draw_line(top_l, by, bot_l, eave_y, c_roof_l)
    canvas.draw_line(top_l + 1, by, bot_l + 1, eave_y, c_roof_l)
    # Top ridge cap
    ridge_h = max(2, roof_h // 10)
    canvas.draw_rect(top_l, by, top_r - top_l + 1, ridge_h, c_roof_l, filled=True)
    canvas.draw_rect(top_l, by + ridge_h, top_r - top_l + 1, 1, c_roof_d, filled=True)

    # Shingle texture on main roof and shaded slope
    canvas.scatter(
        bx + 2,
        by + ridge_h + 1,
        bw - 4,
        max(4, roof_h - ridge_h - 3),
        c_roof_d,
        density=0.65,
        seed=seed,
        target_color=c_roof,
        pattern="shingle",
    )
    canvas.scatter(
        sh_top_l,
        by + ridge_h + 1,
        bot_r - sh_top_l,
        max(4, roof_h - ridge_h - 3),
        darken(c_roof_d, 0.82),
        density=0.55,
        seed=seed + 3,
        target_color=c_roof_d,
        pattern="shingle",
    )

    # Horizontal wooden eave fascia beam (flush with bot_l..bot_r so zero 1px overhang spur!)
    fascia_h = max(2, roof_h // 11)
    canvas.draw_rect(bot_l, eave_y - fascia_h + 1, bw, fascia_h, c_wood, filled=True)
    canvas.draw_rect(bot_l, eave_y - fascia_h + 1, bw, 1, c_wood_l, filled=True)
    canvas.draw_rect(bot_l, eave_y, bw, 1, c_wood_d, filled=True)

    # 8. Front Gable Dormer / Peak (for "gable" or "barn")
    if style in ("gable", "farmhouse", "barn"):
        g_half_w = max(8, bw // 5)
        cx_mid = bx + bw // 2
        g_peak_y = by + max(4, roof_h // 5)
        g_base_y = eave_y
        # Gable wall triangle
        canvas.draw_polygon(
            [(cx_mid, g_peak_y), (cx_mid + g_half_w, g_base_y), (cx_mid - g_half_w, g_base_y)],
            c_wall,
            filled=True,
        )
        # Under-gable eave shadow
        for dx in range(-g_half_w + 2, g_half_w - 1):
            gy_edge = g_peak_y + int(abs(dx) * (g_base_y - g_peak_y) / max(1, g_half_w))
            for sy in range(gy_edge + 1, min(g_base_y, gy_edge + 3)):
                canvas.set_pixel(cx_mid + dx, sy, darken(c_wall, 0.78))
        # Gable wooden bargeboards (thick pitched rafters terminating flush with eave fascia)
        rafter_t = max(2, fascia_h)
        for t_off in range(rafter_t):
            y_end = min(eave_y, g_base_y - (rafter_t - 1 - t_off))
            canvas.draw_line(cx_mid, g_peak_y + t_off, cx_mid - g_half_w, y_end, c_wood_l if t_off == 0 else c_wood)
            canvas.draw_line(cx_mid, g_peak_y + t_off, cx_mid + g_half_w, y_end, c_wood_l if t_off == 0 else c_wood_d)

        # Attic round window or barn hayloft opening inside the gable
        attic_r = max(3, min(g_half_w // 3, (g_base_y - g_peak_y) // 4))
        attic_cy = g_peak_y + (g_base_y - g_peak_y) * 2 // 3 - 1
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
        min_cy = max(9, cw // 2 + 4) if op.get("smoke", True) else 2
        cy = max(min_cy, by - max(5, ch // 3))
        # Roof flashing shadow at chimney base
        canvas.draw_rect(cx - 1, cy + ch, cw + 2, 2, darken(c_roof_d, 0.78), filled=True)
        canvas.draw_rect(cx, cy, cw, ch, c_stone, filled=True)
        canvas.draw_rect(cx, cy, max(1, cw // 5), ch, c_stone_l, filled=True)
        canvas.draw_rect(cx + cw - max(1, cw // 5), cy, max(1, cw // 5), ch, c_stone_d, filled=True)
        canvas.scatter(cx + 1, cy + 3, max(2, cw - 2), max(4, ch - 4), c_stone_d, density=0.55, seed=seed + 7, target_color=c_stone, pattern="brick")
        cap_h = max(2, ch // 6)
        canvas.draw_rect(cx - 1, cy, cw + 2, cap_h, c_stone_d, filled=True)
        canvas.draw_rect(cx - 1, cy, cw + 2, 1, c_stone_l, filled=True)
        canvas.last_chimney = (cx + cw // 2, cy)

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

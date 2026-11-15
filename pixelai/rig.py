"""Parametric multi-resolution 4-direction character rig generator (lineless interior)."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten as _brighten, darken as _darken, parse_color
from pixelai.portrait import draw_field_farmer


def draw_portrait_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Draw a deterministic bust portrait with a cozy, clean-pixel silhouette.

    This is intentionally separate from ``char_rig``: portraits need a larger
    facial design language, asymmetric hair, shoulders, clothing planes and
    explicit feature scale rather than a tiny walk-cycle body.
    """
    if op.get("preset") == "field_farmer":
        draw_field_farmer(canvas, x, y, palette, op)
        return
    if op.get("style", "mistria") == "mistria":
        from pixelai.portrait_mistria import draw_mistria_portrait
        draw_mistria_portrait(canvas, x, y, palette, op)
        return

    w = max(48, int(op.get("width", 64)))
    h = max(64, int(op.get("height", 80)))
    scale = min(w, h) / 64.0
    def p(name: str, fallback: str) -> RGBA:
        return parse_color(op.get(name, fallback), palette)
    ink = p("ink", "#2b1b2b")
    skin = p("skin", "#f2c38f")
    skin_l = p("skin_l", "#ffe0aa")
    skin_d = p("skin_d", "#b96d5c")
    hair = p("hair", "#6b3f35")
    hair_l = p("hair_l", "#925442")
    hair_d = p("hair_d", "#402538")
    shirt = p("shirt", "#d9e5d2")
    garment = p("garment", "#704b3b")
    garment_d = p("garment_d", "#4b302e")
    accent = p("accent", "#d69b4b")
    beard = p("beard_color", "#4b302e")
    eye_color = p("eye_color", "#2b1b2b")
    hat = p("hat_color", "#d69b4b")
    hat_l = p("hat_light", "#f1c66b")
    hat_d = p("hat_dark", "#9a613b")
    bg = p("background", "#d6e6cf")
    face_dir = str(op.get("face_dir", "front")).lower()

    def sx(v: float) -> int:
        return max(0, min(canvas.width - 1, x + round(v * scale)))
    def sy(v: float) -> int:
        return max(0, min(canvas.height - 1, y + round(v * scale)))
    def pts(values: list[tuple[float, float]]) -> list[tuple[int, int]]:
        return [(sx(px), sy(py)) for px, py in values]

    if op.get("fill_background", False):
        prev_no_outline = canvas.mark_no_outline
        canvas.mark_no_outline = True
        canvas.draw_rect(sx(0), sy(0), round(w), round(h), bg, filled=True)
        canvas.mark_no_outline = prev_no_outline
    # Shoulders first: broad, readable planes, with a small rim highlight.
    canvas.draw_polygon(pts([(4, 64), (9, 47), (20, 39), (44, 39), (56, 47), (61, 64)]), shirt, filled=True)
    canvas.draw_polygon(pts([(14, 64), (17, 45), (24, 39), (40, 39), (48, 45), (52, 64)]), garment, filled=True)
    canvas.draw_polygon(pts([(17, 46), (24, 39), (28, 44), (24, 49)]), garment_d, filled=True)
    canvas.draw_polygon(pts([(47, 46), (40, 39), (36, 44), (40, 49)]), garment_d, filled=True)
    canvas.draw_rect(sx(29), sy(50), max(2, round(7 * scale)), max(2, round(5 * scale)), accent, filled=True, bevel=True)

    # Cropped forearms give the bust a lived-in, characterful pose instead of
    # ending as a flat triangular torso. Hands remain simple pixel clusters.
    canvas.draw_polygon(pts([(5, 63), (7, 51), (13, 47), (18, 51), (15, 57), (13, 63)]), shirt, filled=True)
    canvas.draw_polygon(pts([(59, 63), (57, 51), (51, 47), (46, 51), (49, 57), (51, 63)]), shirt, filled=True)
    canvas.draw_polygon(pts([(11, 54), (14, 51), (18, 53), (16, 58), (12, 58)]), skin, filled=True)
    canvas.draw_polygon(pts([(53, 54), (50, 51), (46, 53), (48, 58), (52, 58)]), skin, filled=True)
    gesture = str(op.get("gesture", "idle")).lower()
    if gesture == "wave":
        # Raised forearm and open hand, inspired by the expressive asymmetry
        # in the reference portraits. Skin stays in flat pixel planes.
        canvas.draw_polygon(pts([(51, 52), (55, 45), (57, 33), (59, 23), (62, 24), (60, 37), (59, 48), (57, 56)]), skin, filled=True)
        canvas.draw_polygon(pts([(57, 25), (56, 20), (57, 18), (59, 24)]), skin_l, filled=True)
        canvas.draw_polygon(pts([(59, 24), (60, 18), (62, 17), (62, 25)]), skin_l, filled=True)
        canvas.draw_polygon(pts([(61, 25), (62, 21), (63, 21), (63, 27)]), skin_l, filled=True)
        canvas.draw_line(sx(57), sy(33), sx(60), sy(35), skin_d)
        canvas.draw_line(sx(57), sy(22), sx(59), sy(23), skin_d)
        canvas.draw_line(sx(59), sy(21), sx(61), sy(22), skin_d)
    elif gesture == "hip":
        canvas.draw_polygon(pts([(7, 51), (12, 48), (18, 53), (15, 59), (10, 58)]), skin, filled=True)
        canvas.draw_rect(sx(11), sy(55), max(2, round(5 * scale)), max(1, round(2 * scale)), skin_d, filled=True)

    # Neck and face with a deliberate jaw taper instead of an ellipse-only head.
    canvas.draw_polygon(pts([(27, 35), (37, 35), (39, 44), (34, 48), (26, 44)]), skin, filled=True)
    canvas.draw_polygon(pts([(18, 17), (25, 9), (39, 9), (47, 18), (45, 35), (37, 42), (27, 42), (19, 35)]), skin, filled=True)
    canvas.draw_polygon(pts([(19, 30), (24, 37), (29, 41), (25, 39), (20, 34)]), skin_l, filled=True)
    canvas.draw_polygon(pts([(40, 36), (45, 29), (44, 36), (38, 41)]), skin_d, filled=True)
    # Ears and cheek planes keep the face from reading as a blank oval.
    canvas.draw_polygon(pts([(17, 24), (20, 22), (21, 30), (18, 32)]), skin, filled=True)
    canvas.draw_polygon(pts([(43, 23), (47, 25), (46, 31), (43, 30)]), skin, filled=True)
    canvas.draw_rect(sx(18), sy(26), max(1, round(2 * scale)), max(1, round(2 * scale)), skin_d, filled=True)
    canvas.draw_rect(sx(44), sy(26), max(1, round(2 * scale)), max(1, round(2 * scale)), skin_d, filled=True)

    # Hair mass and side locks; leave the face plane unobstructed.
    canvas.draw_polygon(pts([(16, 22), (14, 14), (20, 6), (32, 2), (45, 7), (50, 17), (45, 27), (42, 17), (36, 11), (27, 10), (21, 16), (20, 28)]), hair, filled=True)
    canvas.draw_polygon(pts([(16, 14), (21, 6), (32, 2), (35, 6), (24, 10), (19, 19)]), hair_l, filled=True)
    canvas.draw_polygon(pts([(38, 5), (45, 8), (50, 17), (45, 27), (42, 16)]), hair_d, filled=True)
    canvas.draw_polygon(pts([(15, 19), (19, 24), (20, 39), (16, 34)]), hair_d, filled=True)
    # Short, stepped locks break the large silhouette into the clustered
    # strands visible in the reference portraits.
    canvas.draw_polygon(pts([(19, 7), (23, 4), (25, 6), (22, 12)]), hair_l, filled=True)
    canvas.draw_polygon(pts([(31, 3), (35, 1), (38, 5), (35, 10)]), hair_l, filled=True)
    canvas.draw_polygon(pts([(44, 12), (49, 15), (48, 21), (44, 18)]), hair_d, filled=True)
    if op.get("hat", False):
        canvas.draw_polygon(pts([(22, 9), (24, 4), (29, 1), (36, 2), (41, 6), (42, 10)]), hat, filled=True)
        canvas.draw_polygon(pts([(25, 4), (29, 1), (35, 2), (38, 5), (29, 6)]), hat_l, filled=True)
        canvas.draw_polygon(pts([(16, 10), (23, 7), (33, 8), (42, 8), (49, 11), (47, 14), (34, 13), (23, 13)]), hat_d, filled=True)
        canvas.draw_polygon(pts([(18, 9), (25, 7), (34, 8), (43, 9), (47, 10), (30, 11)]), hat_l, filled=True)
        canvas.draw_rect(sx(35), sy(10), max(1, round(5 * scale)), max(1, round(1 * scale)), hat_d, filled=True)

    if op.get("beard", False):
        canvas.draw_polygon(pts([(25, 33), (29, 35), (36, 34), (38, 37), (34, 41), (28, 40), (25, 37)]), beard, filled=True)
        canvas.draw_polygon(pts([(28, 34), (31, 35), (35, 34), (33, 37), (29, 37)]), skin_d, filled=True)

    # Facial features use physical pixel clusters at portrait resolutions.
    # Scaling every feature by the body factor produced coarse square eyes.
    eye_y = sy(22)
    if w >= 128:
        eye_specs = [(25, 13), (39, 13)]
        if face_dir in ("right", "three_quarter_right", "3q_right"):
            eye_specs = [(27, 10), (40, 14)]
        elif face_dir in ("left", "three_quarter_left", "3q_left"):
            eye_specs = [(24, 14), (37, 10)]
        for logical_x, eye_w in eye_specs:
            ex = sx(logical_x)
            half = eye_w // 2
            canvas.draw_rect(ex - half, eye_y - 2, eye_w, 7, skin_l, filled=True)
            canvas.draw_rect(ex - half, eye_y - 3, eye_w, 2, hair_d, filled=True)
            iris_x = ex + (1 if face_dir in ("right", "three_quarter_right", "3q_right") else -1 if face_dir in ("left", "three_quarter_left", "3q_left") else 0)
            canvas.draw_rect(iris_x - 1, eye_y - 2, 5, 7, eye_color, filled=True)
            canvas.set_pixel(iris_x, eye_y - 1, (255, 246, 220, 255))
            canvas.set_pixel(ex + half - 1, eye_y + 4, skin_d)
        canvas.draw_rect(sx(23), sy(18), 17, 3, hair_d, filled=True)
        canvas.draw_rect(sx(36), sy(18), 17, 3, hair_d, filled=True)
        nose_shift = 2 if face_dir in ("right", "three_quarter_right", "3q_right") else -2 if face_dir in ("left", "three_quarter_left", "3q_left") else 0
        nx, ny = sx(32) + nose_shift, sy(27)
        canvas.draw_line(nx, ny - 2, nx - 1, ny + 4, skin_d)
        canvas.draw_line(nx - 1, ny + 4, nx + 4, ny + 4, skin_d)
        canvas.set_pixel(nx + 2, ny + 3, skin_l)
        my = sy(34)
        mouth_shift = 1 if nose_shift > 0 else -1 if nose_shift < 0 else 0
        canvas.draw_line(sx(30) + mouth_shift, my, sx(36) + mouth_shift, my, skin_d)
        canvas.set_pixel(sx(33) + mouth_shift, my + 1, skin_l)
    else:
        for eye_x in (24, 38):
            canvas.draw_rect(sx(eye_x - 2), eye_y, max(3, round(6 * scale)), max(3, round(4 * scale)), skin_l, filled=True)
            canvas.draw_rect(sx(eye_x), eye_y, max(2, round(2.5 * scale)), max(3, round(3 * scale)), eye_color, filled=True)
            canvas.set_pixel(sx(eye_x), eye_y, skin_l)
        canvas.draw_line(sx(23), sy(19), sx(29), sy(18), hair_d)
        canvas.draw_line(sx(36), sy(18), sx(42), sy(19), hair_d)
        canvas.draw_rect(sx(31), sy(27), max(1, round(5 * scale)), max(1, round(2 * scale)), skin_d, filled=True)
        canvas.draw_line(sx(30), sy(34), sx(36), sy(34), skin_d)
    # Shirt collar and neck seam provide the layered construction visible in
    # the source portraits without introducing forbidden dark interior ink.
    canvas.draw_polygon(pts([(24, 40), (30, 46), (27, 49), (21, 42)]), shirt, filled=True)
    canvas.draw_polygon(pts([(36, 46), (42, 40), (45, 42), (39, 49)]), shirt, filled=True)
    # Restrained garment folds: colored planes, never interior ink outlines.
    canvas.draw_polygon(pts([(19, 47), (23, 45), (26, 63), (22, 63)]), garment_d, filled=True)
    canvas.draw_polygon(pts([(45, 47), (41, 45), (38, 63), (42, 63)]), garment_d, filled=True)
    canvas.draw_polygon(pts([(27, 44), (31, 47), (35, 44), (37, 63), (25, 63)]), garment, filled=True)
    canvas.draw_rect(sx(29), sy(52), max(2, round(6 * scale)), max(1, round(4 * scale)), garment_d, filled=True)
    canvas.draw_rect(sx(30), sy(52), max(1, round(4 * scale)), max(1, round(1 * scale)), accent, filled=True)


def draw_char_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Draw a native-resolution character rig (size=16..128) facing down, up, left, or right."""
    size = max(16, int(op.get("size", 16)))
    s = size / 16.0
    direction = op.get("dir", "down").lower()
    pose = op.get("pose", "idle").lower()
    frame = int(op.get("frame", 0)) % 4

    def sc(val: float) -> int:
        return max(1, int(round(val * s)))

    def pt(px: float, py: float) -> tuple[int, int]:
        return (x + int(round(px * s)), by + int(round(py * s)))

    skin = parse_color(op.get("skin", "cream" if "cream" in palette else "#f5c6a5"), palette)
    skin_d = _darken(skin, 0.86)
    hair = parse_color(op.get("hair", "wood_d" if "wood_d" in palette else "#6e422c"), palette)
    eye = parse_color(op.get("eye", "ink" if "ink" in palette else "#21181b"), palette)
    shirt = parse_color(op.get("shirt", "roof" if "roof" in palette else "#c24b38"), palette)
    pants = parse_color(op.get("pants", "water_d" if "water_d" in palette else "#326496"), palette)
    shoes = parse_color(op.get("shoes", "soil_d" if "soil_d" in palette else "#5c3c28"), palette)
    hat = parse_color(op["hat"], palette) if "hat" in op else None
    hat_d = _darken(hat, 0.82) if hat else None
    hat_l = _brighten(hat, 1.12) if hat else None
    shirt_d = _darken(shirt, 0.80)
    pants_d = _darken(pants, 0.80)
    pants_l = _brighten(pants, 1.15)
    tool_col = parse_color(op.get("tool", "stone_l" if "stone_l" in palette else "#b5bfd1"), palette)
    handle_col = parse_color(op.get("handle", "wood" if "wood" in palette else "#9c603c"), palette)

    bob = -max(1, int(round(0.5 * s))) if (pose == "walk" and frame in (1, 3)) else 0
    if pose == "work" and frame == 2:
        bob = max(1, int(round(0.5 * s)))
    by = y + bob

    # If facing UP and working, draw tool behind body first
    if pose == "work" and direction == "up":
        _draw_tool_front_back(canvas, x, by, s, frame, handle_col, tool_col, is_up=True)

    # Legs & Boots
    l_len, r_len = sc(2.2), sc(2.2)
    if pose == "walk":
        if frame == 1:
            l_len, r_len = sc(1.2), sc(2.2)
        elif frame == 3:
            l_len, r_len = sc(2.2), sc(1.2)

    leg_y = by + int(round(11.5 * s))
    if direction in ("down", "up"):
        lx, rx_pos = x + int(round(5 * s)), x + int(round(9 * s))
        lw = sc(2)
        canvas.draw_rect(lx, leg_y, lw, l_len, pants_d)
        canvas.draw_rect(lx, leg_y + l_len, lw, sc(1), shoes)
        canvas.draw_rect(rx_pos, leg_y, lw, r_len, pants)
        canvas.draw_rect(rx_pos, leg_y + r_len, lw, sc(1), shoes)
    else:
        stride = sc(1) if (pose == "walk" and frame == 1) else (-sc(1) if (pose == "walk" and frame == 3) else 0)
        cx_leg = x + int(round(7 * s))
        lw = sc(2)
        canvas.draw_rect(cx_leg - stride, leg_y, lw, sc(2), pants_d)
        canvas.draw_rect(cx_leg - stride, leg_y + sc(2), lw, sc(1), shoes)
        canvas.draw_rect(cx_leg + stride, leg_y, lw, sc(2), pants)
        canvas.draw_rect(cx_leg + stride, leg_y + sc(2), lw, sc(1), shoes)

    # Torso & Overalls
    torso_y = by + int(round(7.8 * s))
    torso_h = sc(4)
    if direction in ("down", "up"):
        tx = x + int(round(5 * s))
        tw = sc(6)
        canvas.draw_rect(tx, torso_y, tw, torso_h, shirt)
        canvas.draw_rect(x + int(round(5.5 * s)), torso_y + sc(1), sc(5), torso_h - sc(1), pants)
        if size >= 32 and direction == "down":
            # Straps, buttons, and pocket for high-res rigs
            canvas.draw_rect(x + int(round(5.5 * s)), torso_y, sc(1), sc(1.5), pants_l)
            canvas.draw_rect(x + int(round(9.5 * s)), torso_y, sc(1), sc(1.5), pants_l)
            canvas.draw_rect(x + int(round(6.5 * s)), torso_y + sc(1.8), sc(3), sc(1.5), pants_d)
    else:
        tx = x + int(round(6 * s))
        tw = sc(4)
        canvas.draw_rect(tx, torso_y, tw, torso_h, shirt)
        canvas.draw_rect(tx, torso_y + sc(1), tw, torso_h - sc(1), pants)

    # Head & Face
    head_y = by + int(round(4.5 * s))
    head_x = x + int(round(5 * s))
    head_w = sc(6)
    head_h = sc(3.5)
    if size >= 32:
        canvas.draw_circle(x + int(round(8 * s)), by + int(round(6.2 * s)), sc(3.2), skin if direction != "up" else hair, filled=True)
        if direction != "up":
            canvas.draw_rect(head_x, by + int(round(7.2 * s)), head_w, sc(0.8), skin_d)
    else:
        canvas.draw_rect(head_x, head_y, head_w, head_h, hair if direction == "up" else skin)

    if direction == "down":
        ey = by + int(round(5.8 * s))
        ew, eh = sc(0.8), max(1, int(round(1.2 * s)))
        canvas.draw_rect(x + int(round(6.2 * s)), ey, ew, eh, eye)
        canvas.draw_rect(x + int(round(9.0 * s)), ey, ew, eh, eye)
        if size >= 32:
            canvas.set_pixel(x + int(round(6.2 * s)), ey, (255, 245, 228, 255))
            canvas.set_pixel(x + int(round(9.0 * s)), ey, (255, 245, 228, 255))
    elif direction == "left":
        canvas.draw_rect(x + int(round(9 * s)), head_y, sc(2), head_h, hair)
        canvas.draw_rect(x + int(round(6 * s)), by + int(round(5.8 * s)), sc(0.8), sc(1.2), eye)
    elif direction == "right":
        canvas.draw_rect(x + int(round(5 * s)), head_y, sc(2), head_h, hair)
        canvas.draw_rect(x + int(round(9.2 * s)), by + int(round(5.8 * s)), sc(0.8), sc(1.2), eye)

    # Hat or Hair Crown
    if hat:
        if size >= 32:
            canvas.draw_polygon([pt(4.5, 4.2), pt(11.5, 4.2), pt(10.2, 1.8), pt(5.8, 1.8)], hat, filled=True)
            if hat_l:
                canvas.draw_rect(x + int(round(5.8 * s)), by + int(round(1.8 * s)), sc(4.4), sc(0.6), hat_l)
            canvas.draw_rect(x + int(round(4.8 * s)), by + int(round(3.6 * s)), sc(6.4), sc(0.6), shirt)
            canvas.draw_polygon([pt(2.5, 4.3), pt(13.5, 4.3), pt(12.5, 5.1), pt(3.5, 5.1)], hat_d or hat, filled=True)
        else:
            canvas.draw_rect(x + int(round(5 * s)), by + int(round(2 * s)), sc(6), sc(2), hat)
            canvas.draw_rect(x + int(round(3 * s)), by + int(round(4 * s)), sc(10), sc(1), hat_d or hat)
    else:
        canvas.draw_rect(x + int(round(5 * s)), by + int(round(2 * s)), sc(6), sc(2.5), hair)

    # Arms & Direction-Coherent Tool Animation
    if pose == "work":
        if direction == "down":
            _draw_tool_front_back(canvas, x, by, s, frame, handle_col, tool_col, is_up=False)
        elif direction in ("left", "right"):
            _draw_tool_side(canvas, x, by, s, frame, shirt_d, skin_d, handle_col, tool_col, is_left=(direction == "left"))
    else:
        arm_swing = sc(1) if (pose == "walk" and frame == 1) else (-sc(1) if (pose == "walk" and frame == 3) else 0)
        if direction in ("down", "up"):
            canvas.draw_rect(x + int(round(3.8 * s)), torso_y + arm_swing, sc(1.2), sc(3), shirt_d)
            canvas.draw_rect(x + int(round(11.0 * s)), torso_y - arm_swing, sc(1.2), sc(3), shirt_d)
        else:
            canvas.draw_rect(x + int(round(7 * s)) + arm_swing, torso_y, sc(2), sc(3), shirt_d)


def _draw_tool_front_back(
    canvas: Canvas,
    x: int,
    by: int,
    s: float,
    frame: int,
    handle_col: RGBA,
    tool_col: RGBA,
    is_up: bool,
) -> None:
    """Swing tool vertically centered along body axis (for dir='down' or 'up')."""
    cx = x + int(round(8 * s))
    hw = max(1, int(round(0.8 * s)))
    bw, bh = max(2, int(round(2.6 * s))), max(2, int(round(1.4 * s)))

    if frame == 0:  # Overhead windup
        y_top, y_bot = by + int(round(1 * s)), by + int(round(8.5 * s))
        Blade_y = y_top
    elif frame == 1:  # Mid swing
        y_top, y_bot = by + int(round(5 * s)), by + int(round(10.5 * s))
        Blade_y = y_top
    elif frame == 2:  # Downward impact
        y_top, y_bot = by + int(round(9.5 * s)), by + int(round(14.8 * s))
        Blade_y = y_bot - bh
    else:  # Recover
        y_top, y_bot = by + int(round(8.5 * s)), by + int(round(13.0 * s))
        Blade_y = y_bot - bh

    if is_up and frame in (2, 3):
        y_top, y_bot = by + int(round(2 * s)), by + int(round(7 * s))
        Blade_y = y_top

    canvas.draw_rect(cx - hw // 2, y_top, hw, max(1, y_bot - y_top), handle_col)
    canvas.draw_rect(cx - bw // 2, Blade_y, bw, bh, tool_col)


def _draw_tool_side(
    canvas: Canvas,
    x: int,
    by: int,
    s: float,
    frame: int,
    arm_col: RGBA,
    hand_col: RGBA,
    handle_col: RGBA,
    tool_col: RGBA,
    is_left: bool,
) -> None:
    """Swing tool laterally to the left or right profile."""
    sign = -1 if is_left else 1
    cx = x + int(round(8 * s))
    shoulder_x = cx + sign * int(round(1.5 * s))
    shoulder_y = by + int(round(8.8 * s))

    offsets = [
        (sign * 1.5, -5.0),  # 0: Windup up/back
        (sign * 5.0, -2.5),  # 1: Mid swing
        (sign * 6.0, 2.5),   # 2: Impact low
        (sign * 3.5, 4.0),   # 3: Recover
    ]
    dx_f, dy_f = offsets[frame]
    tip_x = shoulder_x + int(round(dx_f * s))
    tip_y = shoulder_y + int(round(dy_f * s))

    canvas.draw_line(shoulder_x, shoulder_y, tip_x, tip_y, handle_col)
    bw = max(2, int(round(2.0 * s)))
    canvas.draw_rect(tip_x - bw // 2, tip_y - bw // 2, bw, bw, tool_col)
    canvas.draw_rect(
        shoulder_x - max(1, int(round(0.6 * s))),
        shoulder_y,
        max(1, int(round(1.4 * s))),
        max(1, int(round(2.0 * s))),
        arm_col,
    )
    canvas.set_pixel(shoulder_x, shoulder_y + int(round(1.5 * s)), hand_col)

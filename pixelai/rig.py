"""Parametric multi-resolution 4-direction character rig generator (lineless interior)."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import ground_shadow_color, RGBA, brighten as _brighten, darken as _darken, parse_color
from pixelai.portrait import draw_field_farmer


def draw_portrait_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Draw a deterministic cozy RPG bust portrait via `draw_mistria_portrait`."""
    if op.get("preset") == "field_farmer":
        draw_field_farmer(canvas, x, y, palette, op)
        return
    from pixelai.portrait_mistria import draw_mistria_portrait
    draw_mistria_portrait(canvas, x, y, palette, op)


def draw_char_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Draw a native-resolution cozy RPG character rig (size=16..128) in top-down, side, or iso view."""
    size = max(16, int(op.get("size", 16)))
    s = size / 16.0
    raw_dir = op.get("dir", "down").lower()
    pose = op.get("pose", "idle").lower()
    frame = int(op.get("frame", 0)) % 4
    perspective = str(op.get("perspective", "topdown")).lower()
    draw_shadow = bool(op.get("shadow", True))

    is_iso = perspective == "iso" or raw_dir in ("se", "sw", "ne", "nw")
    if "morphology" in op and (perspective != "topdown" or is_iso or size < 32):
        raise ValueError("morphology currently requires a top-down character at native size >= 32")
    if "morphology" in op and (raw_dir not in ("down", "up", "left", "right") or pose not in ("idle", "walk", "run", "work", "attack", "jump", "fall")):
        raise ValueError("morphology requires a supported direction and action")
    if perspective == "topdown" and not is_iso and size >= 32:
        from pixelai.human import draw_topdown_human

        draw_topdown_human(canvas, x, y, size, raw_dir, pose, frame, palette, op)
        return
    iso_dir = raw_dir
    if raw_dir in ("se", "sw", "ne", "nw"):
        direction = {"se": "right", "sw": "left", "ne": "up", "nw": "up"}[raw_dir]
    else:
        direction = raw_dir
        if is_iso:
            iso_dir = {"down": "se", "right": "se", "left": "sw", "up": "ne"}.get(raw_dir, "se")

    def sc(val: float) -> int:
        return max(1, int(round(val * s)))

    def px_i(val: float) -> int:
        return x + int(round(val * s))

    def py_i(val: float) -> int:
        return by + int(round(val * s))

    def pt(px_v: float, py_v: float) -> tuple[int, int]:
        return (px_i(px_v), py_i(py_v))

    default_skin = "skin" if "skin" in palette else "#f5c6a5"
    skin = parse_color(op.get("skin", default_skin), palette)
    # Warm-shifted peach shadow instead of muddy gray darken
    skin_d = (max(0, skin[0] - 36), max(0, skin[1] - 50), max(0, skin[2] - 54), skin[3])
    skin_blush = (min(255, skin[0]), max(0, skin[1] - 56), max(0, skin[2] - 42), skin[3])

    hair = parse_color(op.get("hair", "wood_d" if "wood_d" in palette else "#6e422c"), palette)
    hair_l = _brighten(hair, 1.24)
    hair_d = _darken(hair, 0.72)

    eye = parse_color(op.get("eye", "ink" if "ink" in palette else "#21181b"), palette)
    eye_glint = (255, 248, 240, 255)
    shirt = parse_color(op.get("shirt", "roof" if "roof" in palette else "#c24b38"), palette)
    shirt_l = _brighten(shirt, 1.15)
    shirt_d = _darken(shirt, 0.78)
    collar_col = parse_color("cream" if "cream" in palette else "#f4e8d1", palette)

    pants = parse_color(op.get("pants", "water_d" if "water_d" in palette else "#326496"), palette)
    pants_d = _darken(pants, 0.76)
    pants_l = _brighten(pants, 1.16)

    shoes = parse_color(op.get("shoes", "soil_d" if "soil_d" in palette else "#4e3322"), palette)
    shoes_l = _brighten(shoes, 1.2)
    belt_col = parse_color("wood_d" if "wood_d" in palette else "#5c3c24", palette)
    buckle_col = parse_color("wheat" if "wheat" in palette else "#f4b41b", palette)

    hat = parse_color(op["hat"], palette) if "hat" in op else None
    hat_d = _darken(hat, 0.80) if hat else None
    hat_l = _brighten(hat, 1.16) if hat else None
    tool_col = parse_color(op.get("tool", "stone_l" if "stone_l" in palette else "#b5bfd1"), palette)
    handle_col = parse_color(op.get("handle", "wood" if "wood" in palette else "#9c603c"), palette)
    shadow_col = ground_shadow_color(parse_color(op.get("shadow_color", "shadow" if "shadow" in palette else "#33293a"), palette))

    if draw_shadow:
        prev_sh, prev_no = canvas.mark_shadow, canvas.mark_no_outline
        canvas.mark_shadow = True
        canvas.mark_no_outline = True
        sh_rx = sc(2.6) if pose in ("jump", "fall") else sc(3.8)
        sh_ry = max(1, sc(1.1 if is_iso else 1.0))
        canvas.draw_ellipse(px_i(8), y + int(round(14.5 * s)), sh_rx, sh_ry, shadow_col, filled=True)
        canvas.mark_shadow, canvas.mark_no_outline = prev_sh, prev_no

    bob = 0
    if pose in ("walk", "run") and frame in (1, 3):
        bob = -max(1, int(round((0.8 if pose == "run" else 0.5) * s)))
    elif pose == "idle" and frame == 2:
        bob = max(1, int(round(0.35 * s)))
    elif pose == "jump":
        bob = -max(1, int(round(1.6 * s)))
    elif pose == "fall":
        bob = -max(1, int(round(0.7 * s)))
    elif pose in ("work", "attack") and frame == 2:
        bob = max(1, int(round(0.5 * s)))
    by = y + bob

    if pose in ("work", "attack") and direction == "up":
        _draw_tool_front_back(canvas, x, by, s, frame, handle_col, tool_col, is_up=True)

    # 1. Legs & Boots
    l_len, r_len = sc(2.0), sc(2.0)
    if pose in ("walk", "run"):
        short_len = sc(0.9 if pose == "run" else 1.2)
        if frame == 1:
            l_len, r_len = short_len, sc(2.0)
        elif frame == 3:
            l_len, r_len = sc(2.0), short_len
    elif pose == "jump":
        l_len, r_len = sc(1.2), sc(1.6)
    elif pose == "fall":
        l_len, r_len = sc(1.7), sc(1.3)

    leg_y = by + int(round(11.3 * s))
    if is_iso:
        # True 3/4 isometric staggered feet (front foot forward/down, back foot back/up)
        flip_h = -1 if iso_dir in ("sw", "nw") else 1
        stride = (1 if frame == 1 else (-1 if frame == 3 else 0)) * (1.5 if pose == "run" else 1.0)
        bx_f = 8.0 + flip_h * (1.2 + stride * 0.8)
        bx_b = 8.0 - flip_h * (1.3 + stride * 0.8)
        by_f = leg_y + sc(0.4)
        by_b = leg_y - sc(0.5)
        lw = sc(1.9)
        canvas.draw_rect(px_i(bx_b - 0.9), by_b, lw, l_len, pants_d)
        canvas.draw_rect(px_i(bx_b - 0.9), by_b + l_len, lw, sc(1.1), shoes)
        canvas.draw_rect(px_i(bx_f - 0.9), by_f, lw, r_len, pants)
        canvas.draw_rect(px_i(bx_f - 0.9), by_f + r_len, lw, sc(1.1), shoes_l if s >= 1.5 else shoes)
    elif direction in ("down", "up"):
        lx, rx_pos = px_i(5.2), px_i(9.0)
        lw = sc(1.9)
        canvas.draw_rect(lx, leg_y, lw, l_len, pants_d)
        canvas.draw_rect(lx, leg_y + l_len, lw, sc(1.1), shoes_l if size >= 32 else shoes)
        canvas.draw_rect(rx_pos, leg_y, lw, r_len, pants)
        canvas.draw_rect(rx_pos, leg_y + r_len, lw, sc(1.1), shoes_l if size >= 32 else shoes)
    else:
        stride_scale = 1.7 if pose == "run" else 1.1
        stride = sc(stride_scale) if (pose in ("walk", "run") and frame == 1) else (-sc(stride_scale) if (pose in ("walk", "run") and frame == 3) else 0)
        if pose in ("jump", "fall"):
            stride = sc(1.2)
        cx_leg = px_i(7.0)
        lw = sc(1.9)
        canvas.draw_rect(cx_leg - stride, leg_y, lw, sc(2.0), pants_d)
        canvas.draw_rect(cx_leg - stride, leg_y + sc(2.0), lw, sc(1.1), shoes)
        canvas.draw_rect(cx_leg + stride, leg_y, lw, sc(2.0), pants)
        canvas.draw_rect(cx_leg + stride, leg_y + sc(2.0), lw, sc(1.1), shoes_l if size >= 32 else shoes)

    # 2. Cozy Layered Torso (Collar + Shirt + Overalls/Belt)
    torso_y = py_i(7.7)
    torso_h = sc(3.8)
    if is_iso or direction in ("down", "up"):
        tx = px_i(4.8)
        tw = sc(6.4)
        canvas.draw_polygon([pt(5.5, 7.7), pt(10.4, 7.7), pt(11.2, 8.7), pt(10.5, 11.5), pt(5.4, 11.5), pt(4.8, 8.7)], shirt, filled=True)
        canvas.draw_polygon([pt(5.6, 7.7), pt(10.2, 7.7), pt(10.6, 8.4), pt(5.2, 8.4)], shirt_l, filled=True)
        canvas.draw_rect(px_i(5.3), torso_y + sc(1.3), sc(5.4), torso_h - sc(1.3), pants)
        # Belt + brass buckle or overalls straps
        canvas.draw_rect(px_i(5.2), torso_y + sc(1.3), sc(5.6), max(1, sc(0.6)), belt_col)
        if size >= 32:
            canvas.draw_rect(px_i(5.6), torso_y + sc(0.1), sc(1.0), sc(1.4), pants_l)
            canvas.draw_rect(px_i(9.4), torso_y + sc(0.1), sc(1.0), sc(1.4), pants_l)
        if direction != "up" and not (is_iso and iso_dir in ("ne", "nw")):
            canvas.draw_rect(px_i(7.1), torso_y, sc(1.8), sc(0.9), collar_col)
            canvas.draw_rect(px_i(7.3), torso_y + sc(1.3), sc(1.4), max(1, sc(0.6)), buckle_col)
    else:
        tx = px_i(5.6)
        tw = sc(4.8)
        canvas.draw_polygon([pt(6.2, 7.7), pt(9.6, 7.7), pt(10.4, 8.6), pt(9.8, 11.5), pt(6.0, 11.5), pt(5.6, 8.6)], shirt, filled=True)
        canvas.draw_polygon([pt(6.3, 7.7), pt(9.5, 7.7), pt(9.9, 8.4), pt(5.9, 8.4)], shirt_l, filled=True)
        canvas.draw_rect(tx, torso_y + sc(1.3), tw, torso_h - sc(1.3), pants)
        canvas.draw_rect(tx, torso_y + sc(1.3), tw, max(1, sc(0.6)), belt_col)

    # 3. Safe positive arm kinematics (arms swing at torso/hip level, never onto cheeks)
    swing_scale = 1.1 if pose == "run" else 0.7
    arm_swing = sc(swing_scale) if (pose in ("walk", "run") and frame == 1) else (-sc(swing_scale) if (pose in ("walk", "run") and frame == 3) else 0)
    l_drop = sc(0.8) if arm_swing > 0 else 0
    r_drop = sc(0.8) if arm_swing < 0 else 0

    # 4. Rounded Chibi Head & Expressive Eyes (NO horizontal gray face bar!)
    head_cx = px_i(8.0)
    head_cy = py_i(5.3)
    head_rx = sc(3.8)
    head_ry = sc(2.8)
    is_back = direction == "up" or (is_iso and iso_dir in ("ne", "nw"))

    # Back hair volume underneath head for fullness
    canvas.draw_ellipse(head_cx, py_i(4.0), sc(4.2), sc(2.8), hair_d, filled=True)

    # Ears
    if not is_iso and direction in ("down", "up"):
        canvas.draw_rect(px_i(3.6), py_i(5.2), max(1, sc(0.9)), max(1, sc(1.4)), skin_d if direction == "up" else skin)
        canvas.draw_rect(px_i(11.6), py_i(5.2), max(1, sc(0.9)), max(1, sc(1.4)), skin_d if direction == "up" else skin)

    # Main head silhouette (clean smooth cheeks and chin, no chin mustache bar)
    canvas.draw_ellipse(head_cx, head_cy, head_rx, head_ry, hair if is_back else skin, filled=True)

    # Eyes & Blush
    eye_y = py_i(5.3)
    eh = max(1, sc(1.3))
    ew = max(1, sc(0.9))
    if not is_back:
        if is_iso:
            shift = 1.0 if iso_dir == "se" else -1.0
            e1_x = px_i(6.3 + shift)
            e2_x = px_i(9.1 + shift)
            canvas.draw_rect(e1_x, eye_y, ew, eh, eye)
            canvas.draw_rect(e2_x, eye_y, ew, eh, eye)
            if size >= 32:
                canvas.set_pixel(e1_x, eye_y, eye_glint)
                canvas.set_pixel(e2_x, eye_y, eye_glint)
                canvas.set_pixel(e1_x - 1 if shift < 0 else e2_x + ew, eye_y + eh, skin_blush)
        elif direction == "down":
            e1_x, e2_x = px_i(5.9), px_i(9.3)
            canvas.draw_rect(e1_x, eye_y, ew, eh, eye)
            canvas.draw_rect(e2_x, eye_y, ew, eh, eye)
            if size >= 32:
                canvas.set_pixel(e1_x, eye_y, eye_glint)
                canvas.set_pixel(e2_x, eye_y, eye_glint)
                canvas.draw_rect(e1_x - sc(0.7), eye_y + eh, max(1, sc(0.8)), max(1, sc(0.5)), skin_blush)
                canvas.draw_rect(e2_x + ew, eye_y + eh, max(1, sc(0.8)), max(1, sc(0.5)), skin_blush)
        elif direction == "left":
            ex_l = px_i(5.5)
            canvas.draw_rect(ex_l, eye_y, ew, eh, eye)
            if size >= 32:
                canvas.set_pixel(ex_l, eye_y, eye_glint)
                canvas.set_pixel(ex_l + ew, eye_y + eh, skin_blush)
        elif direction == "right":
            ex_r = px_i(9.6)
            canvas.draw_rect(ex_r, eye_y, ew, eh, eye)
            if size >= 32:
                canvas.set_pixel(ex_r, eye_y, eye_glint)
                canvas.set_pixel(ex_r - max(1, sc(0.6)), eye_y + eh, skin_blush)

    # 5. Layered Bangs, Side Locks, or Cozy Hat (never obscure eyes!)
    if not is_back:
        # Swept bangs stay strictly above eye level (y <= 4.0*s)
        bang_ry = max(1, sc(1.1)) if size < 32 else sc(1.4)
        canvas.draw_ellipse(head_cx, py_i(2.6), sc(4.0), bang_ry, hair, filled=True)
        canvas.draw_ellipse(head_cx - sc(0.5), py_i(2.1), sc(2.6), max(1, sc(0.7)), hair_l, filled=True)
        if not is_iso and direction == "left":
            # Back-of-head profile hair tucked cleanly behind temple & ear
            if hat:
                canvas.draw_rect(px_i(10.7), py_i(4.0), max(1, sc(1.2)), sc(1.8), hair)
            else:
                canvas.draw_ellipse(px_i(10.6), py_i(4.8), max(1, sc(1.5)), sc(2.2), hair, filled=True)
            if size >= 24:
                canvas.set_pixel(px_i(9.2), py_i(5.2), skin_d)
        elif not is_iso and direction == "right":
            # Back-of-head profile hair tucked cleanly behind temple & ear
            if hat:
                canvas.draw_rect(px_i(4.1), py_i(4.0), max(1, sc(1.2)), sc(1.8), hair)
            else:
                canvas.draw_ellipse(px_i(5.4), py_i(4.8), max(1, sc(1.5)), sc(2.2), hair, filled=True)
            if size >= 24:
                canvas.set_pixel(px_i(6.8), py_i(5.2), skin_d)
        elif size >= 32:
            # Parted front/3Q bangs & outer temple locks framing cheeks cleanly
            canvas.draw_rect(px_i(4.0), py_i(3.2), sc(1.1), sc(2.8), hair_d)
            canvas.draw_rect(px_i(10.9), py_i(3.2), sc(1.1), sc(2.8), hair_d)
            canvas.draw_polygon([pt(4.5, 2.7), pt(7.5, 2.7), pt(6.1, 4.1), pt(4.4, 3.9)], hair, filled=True)
            canvas.draw_polygon([pt(8.5, 2.7), pt(11.5, 2.7), pt(11.6, 3.9), pt(9.9, 4.1)], hair, filled=True)
    else:
        # Full back hair with top specular band
        canvas.draw_ellipse(head_cx, py_i(4.5), sc(4.2), sc(3.1), hair, filled=True)
        canvas.draw_ellipse(head_cx, py_i(3.0), sc(2.8), sc(1.0), hair_l, filled=True)

    if hat:
        if size >= 32:
            canvas.draw_polygon([pt(4.5, 3.6), pt(11.5, 3.6), pt(10.2, 1.3), pt(5.8, 1.3)], hat, filled=True)
            if hat_l:
                canvas.draw_rect(px_i(5.9), py_i(1.5), sc(4.2), max(1, sc(0.6)), hat_l)
            canvas.draw_rect(px_i(4.8), py_i(3.0), sc(6.4), max(1, sc(0.6)), shirt)
            canvas.draw_polygon([pt(2.6, 3.6), pt(13.4, 3.6), pt(12.2, 4.5), pt(3.8, 4.5)], hat_d or hat, filled=True)
        else:
            canvas.draw_rect(px_i(5), py_i(1.6), sc(6), sc(2), hat)
            canvas.draw_rect(px_i(3), py_i(3.3), sc(10), sc(1), hat_d or hat)

    # 6. Arms & Hands / Tools (clamped below head level)
    if pose in ("work", "attack"):
        if direction == "down":
            _draw_tool_front_back(canvas, x, by, s, frame, handle_col, tool_col, is_up=False)
        elif direction in ("left", "right"):
            _draw_tool_side(canvas, x, by, s, frame, shirt_d, skin, handle_col, tool_col, is_left=(direction == "left"))
    else:
        hand_h = max(1, sc(1.0))
        sleeve_w = max(1, sc(1.2))
        sleeve_h = max(1, sc(2.1))
        if is_iso:
            flip_h = -1 if iso_dir in ("sw", "nw") else 1
            lx_a = px_i(3.6 + flip_h * 0.3)
            rx_a = px_i(11.2 + flip_h * 0.3)
            canvas.draw_rect(lx_a, torso_y + l_drop, sleeve_w, sleeve_h, shirt_d)
            canvas.draw_rect(lx_a, torso_y + l_drop + sleeve_h, sleeve_w, hand_h, skin)
            canvas.draw_rect(rx_a, torso_y + r_drop + sc(0.3), sleeve_w, sleeve_h, shirt)
            canvas.draw_rect(rx_a, torso_y + r_drop + sc(0.3) + sleeve_h, sleeve_w, hand_h, skin)
        elif direction in ("down", "up"):
            lx_a, rx_a = px_i(3.5), px_i(11.3)
            canvas.draw_rect(lx_a, torso_y + l_drop, sleeve_w, sleeve_h, shirt_d)
            canvas.draw_rect(lx_a, torso_y + l_drop + sleeve_h, sleeve_w, hand_h, skin)
            canvas.draw_rect(rx_a, torso_y + r_drop, sleeve_w, sleeve_h, shirt_d)
            canvas.draw_rect(rx_a, torso_y + r_drop + sleeve_h, sleeve_w, hand_h, skin)
        else:
            if pose in ("jump", "fall"):
                ax = px_i(6.2) if direction == "right" else px_i(8.4)
            else:
                shoulder = 8.2 if direction == "left" else 6.4
                ax = px_i(shoulder) + arm_swing
            aw = max(1, sc(1.4))
            ay = torso_y + sc(0.2)
            canvas.draw_rect(ax, ay, aw, max(1, sc(1.2)), shirt)
            canvas.draw_rect(ax, ay + max(1, sc(1.2)), aw, max(1, sc(0.9)), shirt_d)
            canvas.draw_rect(ax, ay + sleeve_h, aw, hand_h, skin)


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

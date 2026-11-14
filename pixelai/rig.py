"""Parametric multi-resolution 4-direction character rig generator (lineless interior)."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten as _brighten, darken as _darken, parse_color


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

"""Parametric 4-direction character rig generator (lineless interior)."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, parse_color


def _darken(c: RGBA, factor: float = 0.78) -> RGBA:
    return (
        max(0, int(c[0] * factor)),
        max(0, int(c[1] * factor)),
        max(0, int(c[2] * factor)),
        c[3],
    )


def draw_char_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Draw a 16x16 chibi character rig facing down, up, left, or right."""
    direction = op.get("dir", "down").lower()
    pose = op.get("pose", "idle").lower()
    frame = int(op.get("frame", 0)) % 4

    skin = parse_color(op.get("skin", "cream" if "cream" in palette else "#fff5e4"), palette)
    hair = parse_color(op.get("hair", "wood_d" if "wood_d" in palette else "#6e422c"), palette)
    eye = parse_color(op.get("eye", "ink" if "ink" in palette else "#21181b"), palette)
    shirt = parse_color(op.get("shirt", "roof" if "roof" in palette else "#c24b38"), palette)
    pants = parse_color(op.get("pants", "water_d" if "water_d" in palette else "#326496"), palette)
    shoes = parse_color(op.get("shoes", "soil_d" if "soil_d" in palette else "#5c3c28"), palette)
    hat = parse_color(op["hat"], palette) if "hat" in op else None
    hat_brim = _darken(hat, 0.82) if hat else None
    shirt_d = _darken(shirt, 0.80)
    pants_d = _darken(pants, 0.80)

    bob = -1 if (pose == "walk" and frame in (1, 3)) else 0
    by = y + bob

    # Head & Hair / Hat (rows 2..8)
    if hat:
        canvas.draw_rect(x + 5, by + 2, 6, 2, hat)
        canvas.draw_rect(x + 3, by + 4, 10, 1, hat_brim or hat)
    else:
        canvas.draw_rect(x + 5, by + 2, 6, 3, hair)

    if direction == "up":
        canvas.draw_rect(x + 5, by + 5, 6, 3, hair)
    elif direction == "down":
        canvas.draw_rect(x + 5, by + 5, 6, 3, skin)
        canvas.set_pixel(x + 6, by + 6, eye)
        canvas.set_pixel(x + 9, by + 6, eye)
    elif direction == "left":
        canvas.draw_rect(x + 5, by + 5, 6, 3, skin)
        canvas.draw_rect(x + 9, by + 5, 2, 3, hair)
        canvas.set_pixel(x + 6, by + 6, eye)
    elif direction == "right":
        canvas.draw_rect(x + 5, by + 5, 6, 3, skin)
        canvas.draw_rect(x + 5, by + 5, 2, 3, hair)
        canvas.set_pixel(x + 9, by + 6, eye)

    # Torso & Arms (rows 8..11)
    arm_swing = 0
    if pose == "walk":
        arm_swing = 1 if frame == 1 else (-1 if frame == 3 else 0)

    if direction in ("down", "up"):
        canvas.draw_rect(x + 5, by + 8, 6, 4, shirt)
        canvas.draw_rect(x + 6, by + 9, 4, 3, pants)
        # Left & right arms
        canvas.draw_rect(x + 4, by + 8 + arm_swing, 1, 3, shirt_d)
        canvas.draw_rect(x + 11, by + 8 - arm_swing, 1, 3, shirt_d)
    else:
        canvas.draw_rect(x + 6, by + 8, 4, 4, shirt)
        canvas.draw_rect(x + 6, by + 9, 4, 3, pants)
        canvas.draw_rect(x + 7 + arm_swing, by + 8, 2, 3, shirt_d)

    # Tool swing for 'work' pose
    if pose == "work":
        tool_col = parse_color(op.get("tool", "stone_l" if "stone_l" in palette else "#b5bfd1"), palette)
        handle_col = parse_color(op.get("handle", "wood" if "wood" in palette else "#9c603c"), palette)
        if frame % 2 == 0:
            canvas.draw_line(x + 11, by + 8, x + 13, by + 4, handle_col)
            canvas.draw_rect(x + 12, by + 3, 3, 2, tool_col)
        else:
            canvas.draw_line(x + 11, by + 9, x + 14, by + 11, handle_col)
            canvas.draw_rect(x + 13, by + 11, 2, 3, tool_col)

    # Legs & Shoes (rows 12..14, seamless attachment to torso)
    l_len, r_len = 2, 2
    if pose == "walk":
        if frame == 1:
            l_len, r_len = 1, 2
        elif frame == 3:
            l_len, r_len = 2, 1

    if direction in ("down", "up"):
        canvas.draw_rect(x + 5, by + 12, 2, l_len, pants_d)
        canvas.draw_rect(x + 5, by + 12 + l_len, 2, 1, shoes)
        canvas.draw_rect(x + 9, by + 12, 2, r_len, pants)
        canvas.draw_rect(x + 9, by + 12 + r_len, 2, 1, shoes)
    else:
        stride = 1 if (pose == "walk" and frame == 1) else (-1 if (pose == "walk" and frame == 3) else 0)
        canvas.draw_rect(x + 7 - stride, by + 12, 2, 2, pants_d)
        canvas.draw_rect(x + 7 - stride, by + 14, 2, 1, shoes)
        canvas.draw_rect(x + 7 + stride, by + 12, 2, 2, pants)
        canvas.draw_rect(x + 7 + stride, by + 14, 2, 1, shoes)

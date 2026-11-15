"""Parametric cozy 2D creature & farm animal rig and pixel-art emote generator."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, parse_color


def draw_emote(
    canvas: Canvas,
    x: int,
    y: int,
    kind: str,
    frame: int = 0,
    palette: dict[str, RGBA] | None = None,
    outline: bool = False,
) -> None:
    """Draw a crisp pixel-art emote icon (heart, angry, sweat, tears, zzz, exclamation, sick)."""
    pal = palette or {}
    red = parse_color("roof", pal) if "roof" in pal else (194, 75, 56, 255)
    red_l = parse_color("roof_l", pal) if "roof_l" in pal else (232, 120, 88, 255)
    blue = parse_color("water_l", pal) if "water_l" in pal else (139, 224, 240, 255)
    blue_d = parse_color("water", pal) if "water" in pal else (79, 164, 196, 255)
    green = parse_color("grass_l", pal) if "grass_l" in pal else (140, 214, 96, 255)
    green_d = parse_color("grass", pal) if "grass" in pal else (88, 156, 76, 255)
    yellow = parse_color("wheat_l", pal) if "wheat_l" in pal else (255, 230, 128, 255)

    prev_no = canvas.mark_no_outline
    canvas.mark_no_outline = not outline

    bob = -(frame % 2)
    ey = y + bob

    if kind == "heart":
        for dx in (1, 3):
            canvas.set_pixel(x + dx, ey, red)
        for dx in range(5):
            canvas.set_pixel(x + dx, ey + 1, red_l if dx == 1 else red)
        for dx in range(1, 4):
            canvas.set_pixel(x + dx, ey + 2, red)
        canvas.set_pixel(x + 2, ey + 3, red)

    elif kind == "angry":
        # 4-corner inward-pointing comic anger vein (💢)
        col = red_l if frame % 2 == 0 else red
        vein_pts = (
            (1, 0), (0, 1), (1, 1),
            (3, 0), (4, 1), (3, 1),
            (0, 3), (1, 4), (1, 3),
            (4, 3), (3, 4), (3, 3),
        )
        for ox, oy in vein_pts:
            canvas.set_pixel(x + ox, y + oy, col)

    elif kind == "exclamation":
        canvas.draw_rect(x, ey, 2, 3, red_l)
        canvas.set_pixel(x, ey, yellow)
        canvas.draw_rect(x, ey + 4, 2, 1, red)

    elif kind == "zzz":
        step = frame % 4
        zy = y - step
        zx = x + (step // 2)
        canvas.draw_line(zx, zy, zx + 2, zy, blue)
        canvas.set_pixel(zx + 1, zy + 1, blue)
        canvas.draw_line(zx, zy + 2, zx + 2, zy + 2, blue_d)
        if step in (1, 2):
            canvas.set_pixel(zx + 3, zy - 2, blue)
            canvas.set_pixel(zx + 4, zy - 2, blue)

    elif kind == "sweat":
        drop_y = y + (frame % 3)
        canvas.set_pixel(x + 1, drop_y, blue)
        canvas.draw_rect(x, drop_y + 1, 2, 2, blue_d)
        canvas.set_pixel(x, drop_y + 1, blue)

    elif kind == "sick":
        step = frame % 4
        by = y - (step // 2)
        canvas.draw_rect(x, by + 2, 2, 2, green)
        canvas.set_pixel(x, by + 2, yellow)
        canvas.set_pixel(x + 3, by - (step % 2), green_d)
        canvas.set_pixel(x + 2, by - 1 - (step % 2), green)

    canvas.mark_no_outline = prev_no


def _resolve_breed_colors(
    palette: dict[str, RGBA], op: dict[str, Any]
) -> tuple[RGBA, RGBA, RGBA]:
    """Resolve (body, shade, deep_shade) colors from variant ('white|brown|golden|dark') or custom keys."""
    variant = str(op.get("variant", "white")).lower()
    if "body" in op:
        b = parse_color(op["body"], palette)
        s = parse_color(op.get("shade", "stone_l"), palette)
        d = parse_color(op.get("deep_shade", "stone"), palette)
        return b, s, d
    if variant == "brown":
        return (
            parse_color("wood_l", palette),
            parse_color("wood", palette),
            parse_color("wood_d", palette),
        )
    if variant == "golden":
        return (
            parse_color("wheat_l", palette),
            parse_color("wheat", palette),
            parse_color("wheat_d", palette),
        )
    if variant == "dark":
        return (
            parse_color("stone", palette),
            parse_color("stone_d", palette),
            parse_color("shadow", palette),
        )
    return (
        parse_color("cream", palette),
        parse_color("stone_l", palette),
        parse_color("stone", palette),
    )


def _should_draw_shadow(op: dict[str, Any] | None) -> bool:
    return bool((op or {}).get("shadow", True))


def _should_draw_emotes(op: dict[str, Any] | None) -> bool:
    return bool((op or {}).get("emotes", True))


def _resolve_ground_prop(op: dict[str, Any] | None, default_kind: str) -> str:
    raw = (op or {}).get("ground_prop", "auto")
    if raw is False:
        return "none"
    if raw is True:
        return default_kind
    val = str(raw).lower()
    if val in ("none", "false", "0"):
        return "none"
    if val == "auto":
        return default_kind
    return val


def _draw_straw_nest(
    canvas: Canvas,
    cx: int,
    cy: int,
    rx: int,
    ry: int,
    palette: dict[str, RGBA],
) -> None:
    """Draw a cozy woven straw nest beneath a resting creature."""
    straw_d = parse_color("wheat_d", palette) if "wheat_d" in palette else (196, 146, 54, 255)
    straw = parse_color("wheat", palette) if "wheat" in palette else (242, 191, 82, 255)
    straw_l = parse_color("wheat_l", palette) if "wheat_l" in palette else (255, 224, 130, 255)
    canvas.draw_ellipse(cx, cy, rx, ry, straw_d, filled=True)
    canvas.draw_ellipse(cx, cy - 1, max(2, rx - 1), max(1, ry - 1), straw, filled=True)
    for ox in range(-rx + 2, rx - 1, 2):
        canvas.set_pixel(cx + ox, cy - 1, straw_l)
    canvas.set_pixel(cx - rx + 1, cy, straw)
    canvas.set_pixel(cx + rx - 1, cy, straw)


def _draw_chicken_side(
    canvas: Canvas,
    ox: int,
    oy: int,
    palette: dict[str, RGBA],
    pose: str,
    frame: int,
    total_frames: int,
    is_left: bool,
    op: dict[str, Any] | None = None,
) -> None:
    """Render side-profile chicken on a 24x24 local grid, then mirror if facing left."""
    local = Canvas(24, 24)
    cream, shade, deep_shade = _resolve_breed_colors(palette, op or {})
    comb = parse_color("roof", palette)
    comb_l = parse_color("roof_l", palette)
    comb_d = parse_color("roof_d", palette)
    beak = parse_color("wheat", palette)
    beak_d = parse_color("wheat_d", palette)
    eye = parse_color("ink", palette)
    shadow = parse_color("shadow", palette)
    water_l = parse_color("water_l", palette)
    water = parse_color("water", palette)
    grass_l = parse_color("grass_l", palette)
    grass = parse_color("grass", palette)

    body_col = cream
    belly_col = shade
    draw_shadow = _should_draw_shadow(op)
    draw_emotes_flag = _should_draw_emotes(op)
    ground_prop = _resolve_ground_prop(op, "seeds")
    nest_prop = bool((op or {}).get("nest_prop", False))

    # 1. Ground shadow (never outlined)
    if draw_shadow:
        local.mark_shadow = True
        if pose in ("nest", "sleep"):
            local.draw_ellipse(11, 20, 5, 1, shadow, filled=True)
        elif (pose == "happy" and (frame % 4) in (1, 2)) or pose in ("jump", "fall"):
            local.draw_ellipse(11, 21, 3, 1, shadow, filled=True)
        else:
            local.draw_ellipse(11, 21, 5, 1, shadow, filled=True)
        local.mark_shadow = False

    if nest_prop and pose in ("nest", "sleep"):
        _draw_straw_nest(local, 11, 19, 7, 2, palette)

    # Pose kinematics
    body_dx, body_dy = 0, 0
    tail_dx, tail_dy = 0, 0
    head_x, head_y = 15, 10
    wing_dy = 0
    hide_legs = pose in ("nest", "sleep")

    if pose == "idle":
        f = frame % 4
        if f in (1, 2):
            body_dy = 1 if f == 2 else 0
            head_y = 11 if f == 2 else 10
            wing_dy = 1 if f == 2 else 0
        elif f == 3:
            tail_dy = -1

    elif pose == "walk":
        f = frame % 4
        if f == 1:
            body_dy = -1
            head_x, head_y = 16, 9
        elif f == 3:
            body_dy = -1
            head_x, head_y = 15, 9

    elif pose == "run":
        f = frame % 4
        body_dx = 1
        body_dy = -1 if f in (1, 3) else 0
        tail_dx = -1 if f in (1, 3) else 0
        head_x = 16
        head_y = 10 + body_dy
        wing_dy = -1 if f in (1, 2) else 0

    elif pose == "jump":
        body_dy = -3
        tail_dy = -2
        head_x, head_y = 15, 7
        wing_dy = -2

    elif pose == "fall":
        body_dy = -1
        tail_dy = -2
        head_x, head_y = 15, 10
        wing_dy = -2

    elif pose == "peck":
        f = frame % max(1, total_frames)
        peck_table = [
            (0, 0, 15, 10, 0),   # 0: upright
            (0, -1, 16, 12, 0),  # 1: lean forward
            (1, -2, 17, 15, 1),  # 2: deep peck 1 (beak hits ground)
            (1, -1, 16, 13, 0),  # 3: mid-peck recoil
            (1, -2, 17, 15, 1),  # 4: deep peck 2
            (0, -1, 16, 11, 0),  # 5: recover upright
        ]
        body_dy, tail_dy, head_x, head_y, wing_dy = peck_table[f % len(peck_table)]
        if f in (2, 4) and ground_prop != "none":
            local.mark_no_outline = True
            if ground_prop == "grass":
                local.set_pixel(21, 20, grass)
                local.set_pixel(22, 19, grass_l)
                local.set_pixel(20, 19, grass_l)
            else:
                local.set_pixel(21, 20, beak)
                local.set_pixel(22, 19, parse_color("wheat_l", palette))
            local.mark_no_outline = False

    elif pose in ("nest", "sleep"):
        f = frame % 4
        body_dy = 3 if f in (0, 3) else 4
        tail_dy = 3
        head_x = 15
        head_y = (12 if pose == "sleep" else 11) + (1 if f == 2 else 0)
        wing_dy = 1 if f in (1, 2) else 0

    elif pose == "happy":
        f = frame % 4
        hop = [0, -2, -3, -1][f]
        body_dy = hop
        tail_dy = hop
        head_y = 10 + hop
        wing_dy = -1 if f in (1, 2) else 0

    elif pose == "angry":
        f = frame % 4
        body_dx = -1 if f % 2 == 1 else 0
        tail_dy = -1
        head_x, head_y = 16 + body_dx, 10
        wing_dy = -1 if f % 2 == 1 else 0

    elif pose == "sad":
        f = frame % 4
        body_dy = 1
        tail_dy = 2
        head_x, head_y = 16, 12 + (1 if f in (1, 2) else 0)
        wing_dy = 1

    elif pose == "sick":
        f = frame % 4
        body_dx = 1 if f % 2 == 1 else 0
        body_dy = 1
        tail_dy = 2
        head_x, head_y = 15 + body_dx, 11
        wing_dy = 1

    # 2. Tail + Plump Body + Neck Bridge + Head (drawn BEFORE legs so belly clip never overwrites legs!)
    bx, by = 10 + body_dx, 14 + body_dy
    local.draw_rect(5 + body_dx + tail_dx, 11 + tail_dy, 3, 3, belly_col)
    local.draw_rect(5 + body_dx + tail_dx, 11 + tail_dy, 2, 2, body_col)
    local.set_pixel(4 + body_dx + tail_dx, 11 + tail_dy, body_col)

    rx_body = 6 if pose in ("nest", "sleep") else 5
    ry_body = 3 if pose in ("nest", "sleep") else 4
    local.draw_ellipse(bx, by, rx_body, ry_body, body_col, filled=True)

    local.draw_line(bx + 2, by - 1, head_x - 1, head_y + 1, body_col)
    local.draw_line(bx + 3, by, head_x, head_y + 1, body_col)
    local.draw_circle(head_x, head_y, 3, body_col, filled=True)

    # 3. Internal shading & wing (clipped strictly inside the opaque body silhouette!)
    local.clip_to_opaque = True
    local.draw_ellipse(bx, by + 3, rx_body, 2, belly_col, filled=True)
    local.draw_ellipse(bx - 1, by + wing_dy, 3, 2, belly_col, filled=True)
    local.draw_rect(bx - 2, by - 1 + wing_dy, 3, 1, body_col)
    if pose == "sick":
        # Pale green sickly face flush + deeper belly shade
        local.draw_ellipse(head_x, head_y - 1, 3, 2, grass_l, filled=True)
        local.set_pixel(head_x + 1, head_y + 1, grass)
    elif pose == "angry":
        local.draw_ellipse(head_x + 1, head_y, 2, 2, comb_l, filled=True)
    elif pose == "happy":
        local.set_pixel(head_x, head_y + 1, comb_l)
    local.clip_to_opaque = False

    # 4. Legs (drawn AFTER belly shading so yellow legs are never overwritten by grey belly!)
    if not hide_legs:
        if pose in ("walk", "run"):
            f = frame % 4
            stride_dx = 1 if pose == "run" else 0
            if f == 0:
                local.draw_rect(9 - stride_dx, 18, 1, 3, beak_d)
                local.set_pixel(10 - stride_dx, 20, beak_d)
                local.draw_rect(13 + stride_dx, 18, 1, 3, beak)
                local.set_pixel(14 + stride_dx, 20, beak)
            elif f == 1:
                local.draw_rect(8 - stride_dx, 18, 1, 3, beak_d)
                local.set_pixel(9 - stride_dx, 20, beak_d)
                local.draw_rect(14 + stride_dx, 17, 1, 3, beak)
                local.set_pixel(15 + stride_dx, 19, beak)
            elif f == 2:
                local.draw_rect(10, 18, 1, 3, beak_d)
                local.set_pixel(11, 20, beak_d)
                local.draw_rect(12, 18, 1, 3, beak)
                local.set_pixel(13, 20, beak)
            else:
                local.draw_rect(10 + stride_dx, 17, 1, 3, beak_d)
                local.set_pixel(11 + stride_dx, 19, beak_d)
                local.draw_rect(14 - stride_dx, 18, 1, 3, beak)
                local.set_pixel(15 - stride_dx, 20, beak)
        elif pose in ("happy", "jump", "fall"):
            hop = body_dy
            local.draw_rect(9, 18 + hop, 1, 3, beak_d)
            local.set_pixel(10, 20 + hop, beak_d)
            local.draw_rect(13, 18 + hop, 1, 3, beak)
            local.set_pixel(14, 20 + hop, beak)
        elif pose == "angry":
            f = frame % 4
            l_stomp = -1 if f == 1 else 0
            r_stomp = -1 if f == 3 else 0
            local.draw_rect(9 + body_dx, 18 + l_stomp, 1, 3 + l_stomp, beak_d)
            local.set_pixel(10 + body_dx, 20 + l_stomp, beak_d)
            local.draw_rect(13 + body_dx, 18 + r_stomp, 1, 3 + r_stomp, beak)
            local.set_pixel(14 + body_dx, 20 + r_stomp, beak)
        else:
            local.draw_rect(9 + body_dx, 18, 1, 3, beak_d)
            local.set_pixel(10 + body_dx, 20, beak_d)
            local.draw_rect(13 + body_dx, 18, 1, 3, beak)
            local.set_pixel(14 + body_dx, 20, beak)

    # 5. Comb, Beak, Wattle
    if pose in ("sad", "sick"):
        # Drooping comb
        local.draw_rect(head_x - 1, head_y - 4, 3, 1, comb_d if pose == "sick" else comb)
        local.set_pixel(head_x + 1, head_y - 5, comb)
    else:
        local.draw_rect(head_x - 1, head_y - 4, 3, 1, comb)
        local.set_pixel(head_x, head_y - 5, comb_l)
        local.set_pixel(head_x - 1, head_y - 5, comb)

    if pose == "peck" and (frame % max(1, total_frames)) in (2, 3, 4):
        local.draw_rect(head_x + 2, head_y + 1, 2, 2, beak)
        local.set_pixel(head_x + 3, head_y + 3, beak_d)
        local.set_pixel(head_x + 1, head_y + 2, comb)
    elif pose == "angry":
        # Open squawking angry beak
        local.draw_rect(head_x + 3, head_y - 1, 2, 1, beak)
        local.draw_rect(head_x + 3, head_y + 1, 2, 1, beak_d)
        local.set_pixel(head_x + 2, head_y + 2, comb)
    else:
        local.draw_rect(head_x + 3, head_y, 2, 1, beak)
        local.set_pixel(head_x + 3, head_y + 1, beak_d)
        local.set_pixel(head_x + 2, head_y + 2, comb)

    # 6. Expressive Eye
    if pose == "sleep":
        local.draw_rect(head_x, head_y, 2, 1, eye)
    elif pose == "happy":
        local.set_pixel(head_x, head_y, eye)
        local.set_pixel(head_x + 1, head_y - 1, eye)
    elif pose == "angry":
        local.set_pixel(head_x + 1, head_y, eye)
        local.set_pixel(head_x, head_y - 1, eye)
        local.set_pixel(head_x - 1, head_y - 2, eye)
    elif pose == "sad":
        local.set_pixel(head_x + 1, head_y, eye)
        local.draw_rect(head_x, head_y - 1, 2, 1, deep_shade)
        # Animated tear stream & ground puddle
        f = frame % 4
        local.mark_no_outline = True
        local.set_pixel(head_x + 1, head_y + 1, water_l)
        drop_y = head_y + 2 + f * 2
        if drop_y <= 19:
            local.draw_rect(head_x + 1, drop_y, 1, 2, water_l)
        if f in (2, 3):
            local.draw_rect(head_x, 20, 3, 1, water)
        local.mark_no_outline = False
    elif pose == "sick":
        local.draw_rect(head_x, head_y, 2, 1, eye)
        local.set_pixel(head_x, head_y - 1, deep_shade)
    else:
        local.set_pixel(head_x + 1, head_y - 1, eye)

    canvas.blit(local, ox, oy, flip_x=is_left)

    # 7. Emotes drawn after blit so text/icons (e.g. ZZZ) are never horizontally backwards
    if draw_emotes_flag:
        ex = ox + (2 if is_left else 18)
        if pose == "sleep":
            draw_emote(canvas, ex, oy + 4, "zzz", frame=frame, palette=palette, outline=False)
        elif pose == "happy":
            draw_emote(canvas, ex, oy + 2, "heart", frame=frame, palette=palette, outline=False)
        elif pose == "angry":
            draw_emote(canvas, ex, oy + 2, "angry", frame=frame, palette=palette, outline=False)
        elif pose == "sick":
            draw_emote(canvas, ex, oy + 3, "sick", frame=frame, palette=palette, outline=False)


def _draw_chicken_front_back(
    canvas: Canvas,
    ox: int,
    oy: int,
    palette: dict[str, RGBA],
    direction: str,
    pose: str,
    frame: int,
    op: dict[str, Any] | None = None,
) -> None:
    """Render 100% symmetrical front ('down') or back ('up') chicken on a 24x24 grid."""
    local = Canvas(24, 24)
    cream, shade, deep_shade = _resolve_breed_colors(palette, op or {})
    comb = parse_color("roof", palette)
    comb_l = parse_color("roof_l", palette)
    beak = parse_color("wheat", palette)
    beak_d = parse_color("wheat_d", palette)
    eye = parse_color("ink", palette)
    shadow = parse_color("shadow", palette)
    cx = 12  # Exact symmetry axis

    f = frame % 4
    body_dy = 0
    head_dy = 0
    wings_up = False
    shadow_rx = 5
    draw_shadow = _should_draw_shadow(op)
    draw_emotes_flag = _should_draw_emotes(op)
    nest_prop = bool((op or {}).get("nest_prop", False))
    ground_prop = _resolve_ground_prop(op, "seeds")

    if pose == "idle":
        if f == 2:
            body_dy = 1
            head_dy = 1
        elif f == 3:
            head_dy = -1
    elif pose in ("walk", "run"):
        if f in (1, 3):
            body_dy = -1
            head_dy = -1
        if pose == "run" and f in (1, 3):
            wings_up = True
    elif pose in ("nest", "sleep"):
        body_dy = 3 if f in (0, 3) else 4
        head_dy = 3 if f != 2 else 4
    elif pose == "peck":
        f6 = frame % 6
        head_dy = (0, 1, 3, 2, 3, 1)[f6]
        body_dy = 1 if f6 in (2, 4) else 0
    elif pose in ("jump", "fall"):
        body_dy = -3 if pose == "jump" else -1
        head_dy = body_dy
        wings_up = True
        shadow_rx = 3
    elif pose == "surprised":
        if f == 0:
            body_dy = 1
            head_dy = 1
        elif f == 1:
            body_dy = -3
            head_dy = -3
            wings_up = True
            shadow_rx = 3
        elif f == 2:
            body_dy = -4
            head_dy = -4
            wings_up = True
            shadow_rx = 2
        else:
            body_dy = -1
            head_dy = -1
            wings_up = True
            shadow_rx = 4

    # 1. Ground shadow (never outlined)
    if draw_shadow:
        local.mark_shadow = True
        local.draw_ellipse(cx, 21, shadow_rx, 1, shadow, filled=True)
        local.mark_shadow = False

    if nest_prop and pose in ("nest", "sleep"):
        _draw_straw_nest(local, cx, 19, 7, 2, palette)

    # 2. Wings + Plump Body + Head FIRST (so belly shading clip never overwrites the yellow legs!)
    by = 15 + body_dy
    if wings_up:
        wy = by - 2 + (1 if f == 2 else 0)
        local.draw_ellipse(cx - 6, wy, 2, 1, cream, filled=True)
        local.draw_ellipse(cx + 6, wy, 2, 1, cream, filled=True)
        local.set_pixel(cx - 8, wy - 1, cream)
        local.set_pixel(cx + 8, wy - 1, cream)
        local.set_pixel(cx - 6, wy + 1, shade)
        local.set_pixel(cx + 6, wy + 1, shade)

    local.draw_ellipse(cx, by, 5, 4, cream, filled=True)
    hy = 10 + head_dy
    local.draw_circle(cx, hy, 3, cream, filled=True)

    # Internal shading clipped strictly to body+head
    local.clip_to_opaque = True
    local.draw_ellipse(cx, by + 3, 5, 2, shade, filled=True)
    if not wings_up:
        local.draw_rect(cx - 5, by - 1, 2, 3, shade)
        local.draw_rect(cx + 4, by - 1, 2, 3, shade)
        local.set_pixel(cx - 4, by - 1, cream)
        local.set_pixel(cx + 4, by - 1, cream)
    local.clip_to_opaque = False

    if direction == "up":
        # Back-of-head shadow under comb + prominent swaying fan tail on the back
        tail_sway = -1 if (pose == "walk" and f == 1) else (1 if (pose == "walk" and f == 3) else 0)
        tx = cx + tail_sway
        local.draw_ellipse(tx, by + 1, 3, 2, deep_shade, filled=True)
        local.draw_ellipse(tx, by - 1, 3, 2, shade, filled=True)
        local.draw_ellipse(tx, by - 2, 2, 2, cream, filled=True)
        local.set_pixel(tx - 2, by - 3, cream)
        local.set_pixel(tx, by - 4, cream)
        local.set_pixel(tx + 2, by - 3, cream)

    # 3. Symmetrical Legs (drawn AFTER belly shading so yellow legs stay 100% visible!)
    if pose in ("nest", "sleep"):
        pass
    elif pose in ("surprised", "jump", "fall") and (pose != "surprised" or f in (1, 2)):
        ly = 18 + body_dy
        local.draw_rect(cx - 3, ly, 1, 3, beak)
        local.set_pixel(cx - 4, ly + 2, beak)
        local.draw_rect(cx + 3, ly, 1, 3, beak)
        local.set_pixel(cx + 4, ly + 2, beak)
    else:
        l_lift = -1 if (pose in ("walk", "run") and f == 1) else 0
        r_lift = -1 if (pose in ("walk", "run") and f == 3) else 0
        l_col = beak if l_lift < 0 else beak_d
        r_col = beak if r_lift < 0 else beak_d
        local.draw_rect(cx - 2, 18 + l_lift, 1, 3 + l_lift, l_col)
        local.set_pixel(cx - 3, 20 + l_lift, l_col)
        local.draw_rect(cx + 2, 18 + r_lift, 1, 3 + r_lift, r_col)
        local.set_pixel(cx + 3, 20 + r_lift, r_col)

    # 4. Symmetrical Comb (centered at cx=12)
    local.draw_rect(cx - 1, hy - 4, 3, 1, comb)
    local.set_pixel(cx, hy - 5, comb_l)

    # 5. Front Face (100% symmetrical around cx=12)
    if direction == "down":
        if pose == "sleep":
            local.draw_rect(cx - 2, hy - 1, 2, 1, eye)
            local.draw_rect(cx + 1, hy - 1, 2, 1, eye)
            local.draw_rect(cx - 1, hy, 3, 1, beak)
            local.set_pixel(cx, hy + 1, beak_d)
        elif pose == "surprised" and f in (1, 2):
            local.draw_rect(cx - 2, hy - 1, 1, 2, eye)
            local.draw_rect(cx + 2, hy - 1, 1, 2, eye)
            local.draw_rect(cx - 1, hy, 3, 1, beak)
            local.set_pixel(cx, hy + 1, comb)
            local.set_pixel(cx, hy + 2, beak_d)
        else:
            local.set_pixel(cx - 2, hy - 1, eye)
            local.set_pixel(cx + 2, hy - 1, eye)
            local.draw_rect(cx - 1, hy, 3, 1, beak)
            local.set_pixel(cx, hy + 1, beak_d)
            local.set_pixel(cx, hy + 2, comb)
        if pose == "peck" and (frame % 6) in (2, 4) and ground_prop != "none":
            local.mark_no_outline = True
            if ground_prop == "grass":
                local.set_pixel(cx, 22, parse_color("grass", palette))
                local.set_pixel(cx - 1, 21, parse_color("grass_l", palette))
            else:
                local.set_pixel(cx, 22, beak)
                local.set_pixel(cx + 1, 22, parse_color("wheat_l", palette))
            local.mark_no_outline = False

    if draw_emotes_flag:
        if pose == "surprised" and f in (1, 2, 3):
            draw_emote(local, 19, 3, "exclamation", frame=f, palette=palette, outline=False)
        elif pose == "sleep":
            draw_emote(local, 18, 3, "zzz", frame=f, palette=palette, outline=False)

    canvas.blit(local, ox, oy)


def _cow_palette(variant: str) -> dict[str, RGBA]:
    """Return cozy cow color dictionary for a given breed variant."""
    v = variant.lower()
    if v == "brown":
        body = (168, 112, 76, 255)
        body_l = (196, 140, 100, 255)
        body_d = (132, 84, 54, 255)
        spot = (242, 230, 212, 255)
    elif v == "cream":
        body = (240, 224, 192, 255)
        body_l = (252, 242, 218, 255)
        body_d = (206, 184, 148, 255)
        spot = (186, 148, 106, 255)
    elif v == "dark":
        body = (78, 70, 74, 255)
        body_l = (104, 94, 98, 255)
        body_d = (56, 48, 52, 255)
        spot = (232, 226, 220, 255)
    else:  # holstein (default)
        body = (250, 246, 238, 255)
        body_l = (255, 255, 252, 255)
        body_d = (214, 204, 192, 255)
        spot = (62, 54, 60, 255)

    return {
        "body": body,
        "body_l": body_l,
        "body_d": body_d,
        "spot": spot,
        "snout": (244, 186, 180, 255),
        "snout_d": (212, 144, 140, 255),
        "horn": (236, 214, 168, 255),
        "horn_d": (196, 168, 120, 255),
        "hoof": (84, 72, 70, 255),
        "udder": (246, 178, 178, 255),
        "eye": (38, 30, 36, 255),
        "eye_hi": (255, 255, 255, 255),
        "sick_tint": (154, 206, 128, 255),
        "shadow": (40, 34, 48, 88),
    }


def _draw_cow_front_back(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    direction: str,
    pose: str,
    frame: int,
    op: dict[str, Any],
) -> None:
    """Render 100% symmetrical 32x32 cozy cow facing down (front) or up (back)."""
    local = Canvas(32, 32)
    c = _cow_palette(str(op.get("variant", "holstein")))
    f = frame % 4
    is_up = direction == "up"

    draw_shadow = _should_draw_shadow(op)
    draw_emotes_flag = _should_draw_emotes(op)

    jump_y = 0
    if pose in ("surprised", "jump", "fall"):
        jump_y = -2 if pose == "jump" else (-1 if pose == "fall" else (0, -2, -1, 0)[f])
    elif pose == "walk":
        jump_y = (0, -1, 0, -1)[f]
    elif pose == "run":
        jump_y = (-1, -2, 0, -1)[f]
    elif pose == "idle":
        jump_y = 1 if f == 2 else 0

    # Ground shadow (no outline)
    if draw_shadow:
        local.mark_no_outline = True
        sh_rx = 6 if jump_y < -1 else 8
        local.draw_ellipse(16, 28, sh_rx, 2, c["shadow"])
        local.mark_no_outline = False

    by = jump_y

    # Legs (4-frame walk/run cycle: alternating left/right leg stride, always visible below body)
    l_off = -1 if (pose in ("walk", "run") and f == 1) else (1 if (pose in ("walk", "run") and f == 3) else 0)
    r_off = -1 if (pose in ("walk", "run") and f == 3) else (1 if (pose in ("walk", "run") and f == 1) else 0)
    if pose in ("surprised", "jump", "fall") and jump_y < 0:
        l_off = r_off = -1

    # Plump body silhouette first, then clip internal shading/spots
    local.draw_ellipse(16, by + 17, 7, 5, c["body"])
    local.clip_to_opaque = True
    local.draw_ellipse(16, by + 14, 6, 3, c["body_l"])
    local.draw_ellipse(16, by + 21, 7, 2, c["body_d"])
    local.draw_rect(10, by + 14, 4, 4, c["spot"])
    local.draw_rect(18, by + 14, 4, 4, c["spot"])
    local.clip_to_opaque = False

    # Left & Right legs drawn after body so both hooves always protrude cleanly below belly
    local.draw_rect(11, by + 22 + l_off, 3, 3, c["body_d"])
    local.draw_rect(11, by + 25 + l_off, 3, 1, c["hoof"])
    local.draw_rect(18, by + 22 + r_off, 3, 3, c["body_d"])
    local.draw_rect(18, by + 25 + r_off, 3, 1, c["hoof"])

    if is_up:
        # Back view: broad head & ears seamlessly above shoulders + swaying tail
        ear_dy = 1 if f in (1, 3) else 0
        local.draw_rect(8, by + 10 + ear_dy, 3, 2, c["spot"])
        local.draw_rect(21, by + 10 + (1 - ear_dy), 3, 2, c["spot"])
        local.draw_rect(11, by + 7, 2, 2, c["horn"])
        local.draw_rect(19, by + 7, 2, 2, c["horn"])
        local.draw_ellipse(16, by + 11, 5, 4, c["body"])
        local.clip_to_opaque = True
        local.draw_ellipse(16, by + 9, 4, 2, c["body_l"])
        local.draw_rect(12, by + 9, 3, 3, c["spot"])
        local.clip_to_opaque = False

        # Swaying tail with dark tuft
        tail_dx = (-1, 0, 1, 0)[f]
        local.draw_rect(15, by + 16, 2, 3, c["body_d"])
        local.draw_rect(15 + tail_dx, by + 19, 2, 3, c["spot"])
    else:
        # Front view: cute face, horns, ears, expressive eyes, rosy snout
        ear_y = by + 10 if pose not in ("surprised", "jump") else by + 8
        local.draw_rect(8, ear_y, 3, 2, c["spot"])
        local.draw_rect(21, ear_y, 3, 2, c["spot"])
        local.draw_rect(11, by + 7, 2, 2, c["horn"])
        local.draw_rect(19, by + 7, 2, 2, c["horn"])
        local.draw_ellipse(16, by + 11, 5, 4, c["body"])
        local.clip_to_opaque = True
        local.draw_ellipse(16, by + 9, 4, 2, c["body_l"])
        local.draw_rect(11, by + 8, 4, 3, c["spot"])
        local.clip_to_opaque = False

        if pose in ("surprised", "jump") and f in (1, 2):
            local.draw_rect(12, by + 10, 2, 2, c["eye_hi"])
            local.set_pixel(12, by + 11, c["eye"])
            local.draw_rect(18, by + 10, 2, 2, c["eye_hi"])
            local.set_pixel(19, by + 11, c["eye"])
        else:
            local.draw_rect(12, by + 10, 2, 2, c["eye"])
            local.set_pixel(12, by + 10, c["eye_hi"])
            local.draw_rect(18, by + 10, 2, 2, c["eye"])
            local.set_pixel(19, by + 10, c["eye_hi"])

        # Rosy snout
        local.draw_ellipse(16, by + 14, 4, 2, c["snout"])
        local.set_pixel(14, by + 14, c["snout_d"])
        local.set_pixel(18, by + 14, c["snout_d"])
        if pose in ("surprised", "jump") and f in (1, 2):
            local.draw_rect(15, by + 15, 2, 1, c["snout_d"])

    canvas.blit(local, x, y)
    if draw_emotes_flag and not is_up and pose in ("surprised", "jump") and f in (1, 2):
        # Safe top margin y >= 2 so emote never touches canvas border y=0
        draw_emote(canvas, x + 22, y + 3, "exclamation", f, palette, outline=False)


def _draw_cow_side(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    pose: str,
    frame: int,
    total_frames: int,
    is_left: bool,
    op: dict[str, Any],
) -> None:
    """Render 32x32 cozy cow in side profile using local Canvas + blit(flip_x=is_left) for 100% symmetry."""
    local = Canvas(32, 32)
    c = _cow_palette(str(op.get("variant", "holstein")))
    f = frame % max(1, total_frames)
    f4 = frame % 4
    is_lying = pose in ("lie", "nest", "sleep")
    draw_shadow = _should_draw_shadow(op)
    draw_emotes_flag = _should_draw_emotes(op)
    ground_prop = _resolve_ground_prop(op, "grass")
    nest_prop = bool(op.get("nest_prop", False))

    # Ground shadow (no outline)
    if draw_shadow:
        local.mark_no_outline = True
        sh_rx = 10 if is_lying else (7 if pose in ("jump", "fall") else 9)
        local.draw_ellipse(16, 27, sh_rx, 2, c["shadow"])
        local.mark_no_outline = False

    if nest_prop and is_lying:
        _draw_straw_nest(local, 15, 25, 11, 3, palette)

    if is_lying:
        # 4 distinct frames: f0 rest, f1 inhale, f2 inhale + ear/tail twitch, f3 exhale + snout twitch
        breathe = -1 if f4 in (1, 2) else 0
        ear_twitch = 1 if f4 == 2 else 0
        tail_twitch = -1 if f4 in (2, 3) else 0
        snout_dx = 1 if (pose != "sleep" and f4 == 3) else 0
        by = 15 + breathe

        # Tail resting behind body
        local.draw_rect(5, by + 6 + tail_twitch, 2, 3, c["body_d"])
        local.draw_rect(5, by + 9 + tail_twitch, 2, 2, c["spot"])

        # Lying body loaf + neck bridge
        local.draw_ellipse(14, by + 6, 8, 5, c["body"])
        hx, hy = 21, by + 1 + (1 if f4 == 1 else 0)
        local.draw_rect(17, hy + 1, 4, 5, c["body"])
        local.draw_ellipse(hx, hy + 2, 4, 4, c["body"])

        # Internal body shading, spots, and tucked legs (strictly inside opaque silhouette)
        local.clip_to_opaque = True
        local.draw_ellipse(14, by + 3, 7, 3, c["body_l"])
        local.draw_ellipse(14, by + 10, 8, 2, c["body_d"])
        local.draw_rect(9, by + 3, 4, 4, c["spot"])
        local.draw_rect(15, by + 3, 3, 4, c["spot"])
        local.draw_rect(11, by + 9, 3, 2, c["hoof"])
        local.draw_rect(18, by + 9, 3, 2, c["hoof"])
        local.draw_rect(hx - 2, hy - 1, 3, 2, c["body_l"])
        local.clip_to_opaque = False

        # Horn, Ear, Snout, Eye
        local.draw_rect(hx - 3, hy - 2, 2, 2, c["horn"])
        local.draw_rect(hx - 4, hy + 1 + ear_twitch, 2, 2, c["spot"])
        local.draw_rect(hx + 2, hy + 2, 4 + snout_dx, 3, c["snout"])
        local.set_pixel(hx + 4 + snout_dx, hy + 3, c["snout_d"])

        if pose == "sleep":
            local.draw_rect(hx, hy + 1, 2, 1, c["eye"])
        else:
            local.draw_rect(hx, hy + 1, 2, 2, c["eye"])
            local.set_pixel(hx, hy + 1, c["eye_hi"])

        canvas.blit(local, x, y, flip_x=is_left)
        if draw_emotes_flag and pose == "sleep":
            ex = x + (3 if is_left else 24)
            draw_emote(canvas, ex, y + 4, "zzz", f4, palette, outline=False)
        return

    # Standing / walking / running / grazing / emote poses
    bob_y = 0
    body_dx = 0
    if pose == "idle":
        bob_y = 1 if f4 == 2 else 0
    elif pose == "walk":
        bob_y = (0, -1, 0, -1)[f4]
    elif pose == "run":
        bob_y = (-1, -2, 0, -1)[f4]
        body_dx = 1 if f4 in (1, 2) else 0
    elif pose == "jump":
        bob_y = -3
    elif pose == "fall":
        bob_y = -1
    elif pose == "happy":
        bob_y = (0, -2, -3, -1)[f4]
    elif pose == "sick":
        body_dx = (0, 1, 0, -1)[f4]
        bob_y = 1 if f4 in (1, 2) else 0
    elif pose == "angry":
        body_dx = -1 if f4 % 2 == 1 else 0
    elif pose == "sad":
        bob_y = 1

    bx = 14 + body_dx
    by = 17 + bob_y

    # 6-frame fluid graze vs emote head offsets
    munch_w = 0
    munch_dy = 0
    ear_dy = 1 if (pose == "idle" and f4 == 2) else 0
    tail_dy = (-1, 0, 1, 0)[f4] if pose in ("idle", "walk", "run", "happy") else 0
    if pose in ("graze", "peck"):
        f6 = f % 6
        # 6 distinct frames: 0 lower, 1 reach grass, 2 tug/bite, 3 lift+chew, 4 chew lower, 5 raise
        head_dy = (2, 5, 6, 4, 5, 1)[f6]
        head_dx = (1, 2, 1, 2, 2, 1)[f6]
        munch_w = 1 if f6 in (1, 3) else 0
        munch_dy = 1 if f6 in (2, 4) else 0
        ear_dy = 1 if f6 in (2, 4) else 0
        tail_dy = -1 if f6 == 3 else (1 if f6 == 5 else 0)
    elif pose == "sad":
        head_dy = 3 + (1 if f4 in (1, 2) else 0)
        head_dx = 0
        ear_dy = 1
        tail_dy = 2
    elif pose == "sick":
        head_dy = 2
        head_dx = 0
        ear_dy = 1
        tail_dy = 2
    elif pose == "angry":
        head_dy = 1
        head_dx = 1
    else:
        head_dy = 0
        head_dx = 0

    hx = 21 + body_dx + head_dx
    hy = 11 + bob_y + head_dy

    # 1. Back legs (slightly darker, drawn behind udder/body)
    fl_off = -2 if (pose in ("walk", "run") and f4 == 1) else (1 if (pose in ("walk", "run") and f4 == 3) else 0)
    fr_off = -2 if (pose in ("walk", "run") and f4 == 3) else (1 if (pose in ("walk", "run") and f4 == 1) else 0)
    bl_off = -2 if (pose in ("walk", "run") and f4 == 3) else 0
    br_off = -2 if (pose in ("walk", "run") and f4 == 1) else 0
    if pose == "run":
        fl_off -= 1 if f4 in (1, 2) else 0
        br_off -= 1 if f4 in (1, 2) else 0
    elif pose == "angry":
        fr_off = -2 if f4 == 1 else 0
        fl_off = -1 if f4 == 3 else 0

    local.draw_rect(9 + body_dx, by + 4 + bl_off, 2, 4, c["body_d"])
    local.draw_rect(9 + body_dx, by + 8 + bl_off, 2, 1, c["hoof"])
    local.draw_rect(18 + body_dx, by + 4 + fl_off, 2, 4, c["body_d"])
    local.draw_rect(18 + body_dx, by + 8 + fl_off, 2, 1, c["hoof"])

    # Udder
    local.draw_rect(12 + body_dx, by + 4, 3, 2, c["udder"])

    # 2. Tail + Body + Thick Neck Bridge + Head (connected silhouette before internal clipping!)
    local.draw_rect(5 + body_dx, by - 1 + tail_dy, 2, 4, c["body_d"])
    local.draw_rect(5 + body_dx, by + 3 + tail_dy, 2, 2, c["spot"])

    local.draw_ellipse(bx, by, 7, 5, c["body"])
    # Thick neck bridge connecting shoulders to lowered/raised head so no internal outline pinches form
    for ny_off in range(-2, 3):
        local.draw_line(bx + 4, by - 2 + ny_off, hx - 1, hy + 2 + ny_off, c["body"])
    local.draw_ellipse(hx, hy + 2, 4, 4, c["body"])

    # 3. Internal shading, spots, and facial flushes (strictly clipped inside opaque silhouette!)
    local.clip_to_opaque = True
    local.draw_ellipse(bx, by - 3, 6, 3, c["body_l"])
    local.draw_ellipse(bx, by + 4, 7, 2, c["body_d"])
    local.draw_rect(bx - 5, by - 3, 3, 4, c["spot"])
    local.draw_rect(bx, by - 4, 3, 3, c["spot"])
    local.draw_rect(hx - 2, hy - 1, 3, 2, c["body_l"])
    if pose == "sick":
        local.draw_ellipse(hx, hy + 1, 3, 2, c["sick_tint"])
    elif pose == "angry":
        local.draw_ellipse(hx + 1, hy + 1, 2, 2, parse_color("roof_l", palette))
    elif pose == "happy":
        local.set_pixel(hx + 1, hy + 3, c["snout"])
    local.clip_to_opaque = False

    # 4. Foreground legs
    local.draw_rect(7 + body_dx, by + 4 + br_off, 2, 4, c["body"])
    local.draw_rect(7 + body_dx, by + 8 + br_off, 2, 1, c["hoof"])
    local.draw_rect(16 + body_dx, by + 4 + fr_off, 2, 4, c["body"])
    local.draw_rect(16 + body_dx, by + 8 + fr_off, 2, 1, c["hoof"])

    # 5. Horn, Ear & Snout
    local.draw_rect(hx - 3, hy - 2, 2, 2, c["horn"])
    local.draw_rect(hx - 4, hy + 1 + ear_dy, 2, 2, c["spot"])
    local.draw_rect(hx + 2, hy + 2 + munch_dy, 4 + munch_w, 3, c["snout"])
    local.set_pixel(hx + 4 + munch_w, hy + 3 + munch_dy, c["snout_d"])

    # Grazing grass blades / seeds & chew detail (outline=False so prop stays delicate)
    if pose in ("graze", "peck") and (f % 6) in (1, 2, 3, 4) and ground_prop != "none":
        local.mark_no_outline = True
        if ground_prop == "seeds":
            seed_c = parse_color("wheat", palette)
            seed_l = parse_color("wheat_l", palette)
            local.set_pixel(hx + 5 + munch_w, hy + 5, seed_l)
            if (f % 6) in (1, 2):
                local.set_pixel(hx + 6 + munch_w, hy + 6, seed_c)
                local.set_pixel(hx + 4 + munch_w, hy + 6, seed_l)
        else:
            grass_c = parse_color("grass", palette)
            grass_l = parse_color("grass_l", palette)
            local.set_pixel(hx + 5 + munch_w, hy + 5, grass_l)
            if (f % 6) in (1, 2):
                local.set_pixel(hx + 6 + munch_w, hy + 6, grass_c)
                local.set_pixel(hx + 4 + munch_w, hy + 6, grass_l)
        local.mark_no_outline = False

    # 6. Expressive Eyes & Secondary FX
    if pose == "angry":
        local.draw_rect(hx, hy + 1, 2, 2, c["eye"])
        local.draw_rect(hx - 1, hy, 3, 1, c["spot"])
        if f4 in (1, 3):
            local.mark_no_outline = True
            local.draw_rect(hx + 6, hy + 2, 2, 2, c["body_l"])
            local.set_pixel(hx + 8, hy + 1, c["body_d"])
            local.mark_no_outline = False
    elif pose == "sick":
        local.draw_rect(hx, hy + 2, 2, 1, c["eye"])
        local.draw_rect(hx, hy + 1, 2, 1, c["spot"])
    elif pose == "happy":
        local.set_pixel(hx, hy + 1, c["eye"])
        local.set_pixel(hx + 1, hy, c["eye"])
    elif pose == "sad":
        local.draw_rect(hx, hy + 2, 2, 1, c["eye"])
        local.mark_no_outline = True
        water_l = parse_color("water_l", palette)
        water = parse_color("water", palette)
        drop_y = hy + 3 + f4 * 2
        if drop_y <= 25:
            local.draw_rect(hx + 1, drop_y, 1, 2, water_l)
        if f4 in (2, 3):
            local.draw_rect(hx, 26, 3, 1, water)
        local.mark_no_outline = False
    else:
        local.draw_rect(hx, hy + 1, 2, 2, c["eye"])
        local.set_pixel(hx, hy + 1, c["eye_hi"])

    canvas.blit(local, x, y, flip_x=is_left)

    # 7. Emotes drawn after blit so icons are never backwards
    if draw_emotes_flag:
        ex = x + (3 if is_left else 23)
        ey = max(y + 2, y + hy - 7)
        if pose == "happy":
            draw_emote(canvas, ex, ey, "heart", f4, palette, outline=False)
        elif pose == "angry":
            draw_emote(canvas, ex, ey, "angry", f4, palette, outline=False)
        elif pose == "sad":
            draw_emote(canvas, ex, ey, "sweat", f4, palette, outline=False)
        elif pose == "sick":
            draw_emote(canvas, ex, ey, "sick", f4, palette, outline=False)


def draw_animal_rig(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
    frame_idx: int = 0,
    total_frames: int = 4,
) -> None:
    """Render a parametric cozy farm animal rig ('chicken' or 'cow')."""
    species = str(op.get("species", "chicken")).lower()
    direction = op.get("dir", "right").lower()
    pose = op.get("pose", "walk").lower()
    frame = int(op.get("frame", frame_idx))
    tot = int(op.get("total_frames", max(1, total_frames)))
    perspective = str(op.get("perspective", "topdown")).lower()

    # Map isometric diagonal directions (se, sw, ne, nw) cleanly
    if direction in ("se", "sw", "ne", "nw") or perspective == "iso":
        iso_map = {"se": "right", "sw": "left", "ne": "up", "nw": "up"}
        direction = iso_map.get(direction, direction)

    if species == "cow":
        if pose == "surprised" or (pose == "jump" and perspective != "platformer") or direction in ("down", "up"):
            eff_dir = "up" if direction == "up" else "down"
            _draw_cow_front_back(canvas, x, y, palette, eff_dir, pose, frame, op=op)
        else:
            _draw_cow_side(
                canvas,
                x,
                y,
                palette,
                pose,
                frame,
                tot,
                is_left=(direction == "left"),
                op=op,
            )
        return

    if pose == "surprised" or (pose == "jump" and perspective != "platformer") or direction in ("down", "up"):
        eff_dir = "up" if direction == "up" else "down"
        _draw_chicken_front_back(canvas, x, y, palette, eff_dir, pose, frame, op=op)
    else:
        _draw_chicken_side(
            canvas,
            x,
            y,
            palette,
            pose,
            frame,
            tot,
            is_left=(direction == "left"),
            op=op,
        )

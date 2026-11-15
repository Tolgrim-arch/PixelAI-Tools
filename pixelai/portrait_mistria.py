"""Fields of Mistria style character portrait generator.

Renders a 3/4 bust portrait at native ~144x160 resolution using organic
pixel-perfect curves, anime-inspired 90s facial proportions, cel-shading
with hue-shifted shadows, and selective colored internal linework (sel-out).
"""

from __future__ import annotations

import math
from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import RGBA, parse_color


def _qbezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    steps: int = 24,
) -> list[tuple[int, int]]:
    """Sample a quadratic Bezier curve into integer pixel coordinates."""
    pts: list[tuple[int, int]] = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1.0 - t
        bx = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
        by = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
        pt = (round(bx), round(by))
        if not pts or pts[-1] != pt:
            pts.append(pt)
    return pts


def _draw_curve(
    canvas: Canvas,
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    color: RGBA,
    thickness: int = 1,
    steps: int = 28,
) -> None:
    """Draw a smooth pixel-perfect quadratic Bezier curve."""
    pts = _qbezier(p0, p1, p2, steps)
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        canvas.draw_line(x0, y0, x1, y1, color)
        if thickness > 1:
            canvas.draw_line(x0, y0 + 1, x1, y1 + 1, color)


def _ellipse_poly(
    cx: float, cy: float, rx: float, ry: float, steps: int = 28
) -> list[tuple[int, int]]:
    """Generate a smooth polygon approximating an ellipse."""
    return [
        (
            round(cx + rx * math.cos(2 * math.pi * i / steps)),
            round(cy + ry * math.sin(2 * math.pi * i / steps)),
        )
        for i in range(steps)
    ]


def _draw_mistria_eye(
    canvas: Canvas,
    cx: int,
    cy: int,
    w: int,
    h: int,
    iris_color: RGBA,
    ink: RGBA,
    skin_d: RGBA,
    facing_right: bool = True,
) -> None:
    """Draw an expressive 90s-anime / Fields of Mistria style eye."""
    hw = w // 2
    hh = h // 2
    white: RGBA = (255, 249, 240, 255)
    pupil: RGBA = (24, 16, 24, 255)

    # Sclera (white of the eye)
    sclera = _ellipse_poly(cx, cy, hw, hh, steps=20)
    canvas.draw_polygon(sclera, white, filled=True)

    # Iris (slightly shifted toward gaze direction, colored)
    gx = 1 if facing_right else -1
    iris_rx = max(2, hw - 2)
    iris_ry = max(2, hh)
    iris_poly = _ellipse_poly(cx + gx, cy, iris_rx, iris_ry, steps=18)
    canvas.draw_polygon(iris_poly, iris_color, filled=True)

    # Pupil (smaller so iris color shows clearly)
    pupil_poly = _ellipse_poly(cx + gx, cy, max(1, iris_rx - 2), max(1, iris_ry - 2), steps=14)
    canvas.draw_polygon(pupil_poly, pupil, filled=True)

    # Upper lash line (thick, curved, characteristic of Mistria)
    _draw_curve(
        canvas,
        (cx - hw - 1, cy - 1),
        (cx, cy - hh - 2),
        (cx + hw + 1, cy - 1),
        ink,
        thickness=2,
        steps=16,
    )
    # Subtle lower lid shadow
    _draw_curve(
        canvas,
        (cx - hw + 1, cy + hh),
        (cx, cy + hh + 1),
        (cx + hw - 1, cy + hh),
        skin_d,
        thickness=1,
        steps=12,
    )

    # Catchlight (bright 2px highlight)
    canvas.set_pixel(cx + gx - 1, cy - 1, white)
    canvas.set_pixel(cx + gx - 1, cy, white)


def draw_mistria_portrait(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Draw a Fields of Mistria style character portrait."""
    w = max(96, int(op.get("width", 144)))
    h = max(112, int(op.get("height", 160)))
    scale = min(w / 144.0, h / 160.0)

    def p(name: str, fallback: str) -> RGBA:
        return parse_color(op.get(name, fallback), palette)

    ink = p("ink", "#1a1218")
    skin = p("skin", "#f2c18e")
    skin_l = p("skin_l", "#ffdfa8")
    skin_d = p("skin_d", "#c67d63")
    hair = p("hair", "#6d4034")
    hair_l = p("hair_l", "#965b45")
    hair_d = p("hair_d", "#42242c")
    shirt = p("shirt", "#e5ead9")
    shirt_d = p("shirt_d", "#b5c2a8")
    garment = p("garment", "#5b483a")
    garment_d = p("garment_d", "#3d2f28")
    accent = p("accent", "#d99b43")
    beard = p("beard_color", "#4a2b2b")
    eye_color = p("eye_color", "#4a7548")
    if eye_color == ink or (eye_color[0] < 45 and eye_color[1] < 45 and eye_color[2] < 45):
        eye_color = (74, 117, 72, 255)
    hat = p("hat_color", "#dcb05a")
    hat_l = p("hat_light", "#f7dc8c")
    hat_d = p("hat_dark", "#a67536")
    bg = p("background", "#d6e6cf")
    face_dir = str(op.get("face_dir", "three_quarter_right")).lower()
    facing_right = face_dir in ("right", "three_quarter_right", "3q_right")

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

    # 1. TORSO & SHOULDERS (broad, natural rounded shoulders)
    torso_pts = (
        _qbezier((16, 159), (18, 120), (34, 104), 12)
        + _qbezier((34, 104), (72, 92), (110, 104), 12)
        + _qbezier((110, 104), (126, 120), (128, 159), 12)
    )
    canvas.draw_polygon(pts(torso_pts), shirt, filled=True)

    # Shirt shoulder shadows & folds
    canvas.draw_polygon(
        pts(_qbezier((16, 159), (18, 125), (34, 106), 10) + [(44, 130), (36, 159)]),
        shirt_d,
        filled=True,
    )
    canvas.draw_polygon(
        pts(_qbezier((110, 106), (126, 125), (128, 159), 10) + [(108, 159), (100, 130)]),
        shirt_d,
        filled=True,
    )

    # Overalls / Vest (garment)
    overalls_pts = (
        [(36, 159), (39, 122), (45, 100), (54, 100), (57, 118)]
        + [(87, 118), (90, 100), (99, 100), (105, 122), (108, 159)]
    )
    canvas.draw_polygon(pts(overalls_pts), garment, filled=True)

    # Overall straps shadow & brass buckles
    canvas.draw_polygon(pts([(44, 100), (53, 100), (56, 122), (42, 122)]), garment_d, filled=True)
    canvas.draw_polygon(pts([(91, 100), (100, 100), (102, 122), (88, 122)]), garment_d, filled=True)
    canvas.draw_rect(sx(45), sy(118), max(3, round(8 * scale)), max(2, round(5 * scale)), accent, filled=True)
    canvas.draw_rect(sx(91), sy(118), max(3, round(8 * scale)), max(2, round(5 * scale)), accent, filled=True)

    # Chest pocket on overalls
    canvas.draw_rect(sx(62), sy(128), max(8, round(20 * scale)), max(6, round(16 * scale)), garment_d, filled=True)
    canvas.draw_rect(sx(63), sy(129), max(6, round(18 * scale)), max(2, round(3 * scale)), accent, filled=True)

    # Sel-out cloth fold lines & rolled-up sleeve cuffs
    _draw_curve(canvas, (sx(28), sy(122)), (sx(34), sy(134)), (sx(32), sy(148)), shirt_d, 1)
    _draw_curve(canvas, (sx(116), sy(122)), (sx(110), sy(134)), (sx(112), sy(148)), shirt_d, 1)
    # Rolled sleeve cuffs + exposed forearms for natural farmer look
    canvas.draw_polygon(pts([(14, 140), (32, 136), (33, 143), (15, 146)]), shirt_d, filled=True)
    canvas.draw_polygon(pts([(15, 146), (31, 143), (29, 159), (16, 159)]), skin, filled=True)
    canvas.draw_polygon(pts([(112, 136), (130, 140), (129, 146), (111, 143)]), shirt_d, filled=True)
    canvas.draw_polygon(pts([(113, 143), (129, 146), (128, 159), (115, 159)]), skin, filled=True)

    # 2. NECK & COLLARBONE
    neck_pts = [(57, 82), (87, 82), (91, 104), (72, 112), (53, 104)]
    canvas.draw_polygon(pts(neck_pts), skin, filled=True)
    # Chin occlusion shadow on neck
    canvas.draw_polygon(
        pts(_qbezier((56, 84), (72, 96), (88, 84), 12) + [(88, 92), (72, 99), (56, 92)]),
        skin_d,
        filled=True,
    )
    # Shirt collar flaps
    canvas.draw_polygon(pts([(46, 98), (58, 96), (64, 108), (50, 108)]), shirt, filled=True)
    canvas.draw_polygon(pts([(98, 98), (86, 96), (80, 108), (94, 108)]), shirt, filled=True)
    _draw_curve(canvas, (sx(58), sy(97)), (sx(64), sy(105)), (sx(72), sy(109)), shirt_d, 1)
    _draw_curve(canvas, (sx(86), sy(97)), (sx(80), sy(105)), (sx(72), sy(109)), shirt_d, 1)

    # 3. HEAD & JAWLINE (organic 3/4 Mistria shape)
    head_pts = (
        _qbezier((47, 46), (48, 24), (72, 24), 10)
        + _qbezier((72, 24), (96, 24), (97, 48), 10)
        + _qbezier((97, 48), (97, 74), (80, 88), 10)
        + _qbezier((80, 88), (66, 91), (52, 78), 10)
        + _qbezier((52, 78), (46, 64), (47, 46), 8)
    )
    canvas.draw_polygon(pts(head_pts), skin, filled=True)

    # Cheek & jaw cel-shading
    canvas.draw_polygon(
        pts(_qbezier((82, 86), (94, 74), (96, 54), 10) + [(92, 68), (84, 80)]),
        skin_d,
        filled=True,
    )
    # Ear (left side in 3/4 right)
    ear_pts = _ellipse_poly(46, 62, 5, 8, steps=16)
    canvas.draw_polygon(pts(ear_pts), skin, filled=True)
    _draw_curve(canvas, (sx(44), sy(58)), (sx(47), sy(62)), (sx(45), sy(66)), skin_d, 1)

    # 4. FACIAL FEATURES (Mistria 90s anime proportions)
    eye_y = sy(58)
    left_eye_x = sx(63) if facing_right else sx(59)
    right_eye_x = sx(84) if facing_right else sx(80)
    _draw_mistria_eye(canvas, left_eye_x, eye_y, round(11 * scale), round(8 * scale), eye_color, ink, skin_d, facing_right)
    _draw_mistria_eye(canvas, right_eye_x, eye_y, round(10 * scale), round(8 * scale), eye_color, ink, skin_d, facing_right)

    # Eyebrows (expressive, slightly arched)
    _draw_curve(canvas, (left_eye_x - 6, eye_y - 8), (left_eye_x, eye_y - 11), (left_eye_x + 6, eye_y - 8), hair_d, 2)
    _draw_curve(canvas, (right_eye_x - 5, eye_y - 8), (right_eye_x, eye_y - 11), (right_eye_x + 5, eye_y - 8), hair_d, 2)

    # Nose (subtle 3/4 anime nose: short bridge + shadow under tip)
    nx = sx(75) if facing_right else sx(69)
    ny = sy(67)
    canvas.draw_line(nx, ny - 3, nx + (2 if facing_right else -2), ny + 1, skin_d)
    canvas.draw_line(nx - 1, ny + 2, nx + 2, ny + 2, skin_d)
    canvas.set_pixel(nx, ny + 1, skin_l)

    # Warm smile
    mx = sx(73) if facing_right else sx(70)
    my = sy(76)
    _draw_curve(canvas, (mx - 6, my - 1), (mx, my + 2), (mx + 6, my - 1), skin_d, 1)
    canvas.draw_line(mx - 2, my + 3, mx + 2, my + 3, skin_d)

    # Optional stubble/beard (connected from sideburns with textured edge)
    if op.get("beard", False):
        beard_pts = (
            _qbezier((50, 66), (62, 89), (89, 74), 12)
            + _qbezier((89, 74), (84, 88), (68, 90), 10)
            + _qbezier((68, 90), (52, 83), (50, 66), 8)
        )
        canvas.draw_polygon(pts(beard_pts), beard, filled=True)
        # Subtle skin/stubble break on chin & upper lip
        canvas.draw_rect(mx - 6, my - 2, 12, 4, skin, filled=True)
        _draw_curve(canvas, (mx - 5, my - 1), (mx, my + 1), (mx + 5, my - 1), skin_d, 1)

    # 5. HAIR (layered curved locks)
    hair_back = (
        _qbezier((42, 60), (38, 30), (68, 18), 12)
        + _qbezier((68, 18), (98, 18), (102, 52), 12)
        + [(96, 56), (92, 36), (72, 30), (50, 38), (46, 58)]
    )
    canvas.draw_polygon(pts(hair_back), hair_d, filled=True)

    # Forehead bangs (asymmetric Mistria locks)
    bangs = (
        _qbezier((45, 48), (50, 26), (74, 24), 10)
        + [(88, 28), (95, 42), (86, 36), (78, 44), (72, 34), (60, 44), (52, 38), (46, 50)]
    )
    canvas.draw_polygon(pts(bangs), hair, filled=True)
    # Hair highlight streak
    _draw_curve(canvas, (sx(52), sy(32)), (sx(68), sy(26)), (sx(84), sy(31)), hair_l, 2)

    # 6. STRAW HAT (optional, curved 3/4 brim + crown + band)
    if op.get("hat", False):
        # Crown
        crown_pts = _qbezier((48, 26), (52, 8), (72, 8), 10) + _qbezier((72, 8), (92, 8), (96, 26), 10)
        canvas.draw_polygon(pts(crown_pts), hat, filled=True)
        # Crown highlight
        canvas.draw_polygon(pts(_qbezier((54, 20), (64, 10), (78, 12), 8) + [(72, 18), (58, 22)]), hat_l, filled=True)
        # Hat band
        canvas.draw_polygon(pts([(48, 23), (96, 23), (97, 28), (47, 28)]), garment, filled=True)
        # Wide curved brim
        brim_pts = (
            _qbezier((24, 34), (72, 20), (120, 34), 16)
            + _qbezier((120, 34), (72, 42), (24, 34), 16)
        )
        canvas.draw_polygon(pts(brim_pts), hat, filled=True)
        _draw_curve(canvas, (sx(28), sy(33)), (sx(72), sy(24)), (sx(116), sy(33)), hat_l, 2)
        _draw_curve(canvas, (sx(26), sy(35)), (sx(72), sy(41)), (sx(118), sy(35)), hat_d, 2)

"""Fields of Mistria style waist-up character portrait generator.

Renders a 3/4 waist-up portrait (~3.5 heads tall) with 90s-anime Mistria facial
proportions, clean L-corner-filtered 1px curves, hue-shifted cel-shading,
colored sel-out cloth folds, and structural ink separation.
"""

from __future__ import annotations

from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten, darken, parse_color


def _qbezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    steps: int = 24,
) -> list[tuple[int, int]]:
    """Sample a quadratic Bezier curve into unique integer pixel coordinates."""
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


def _clean_1px_path(raw: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Strip diagonal-adjacent L-corners so 1px pixel art curves stay crisp."""
    if len(raw) < 3:
        return raw
    out: list[tuple[int, int]] = [raw[0]]
    i = 1
    while i < len(raw) - 1:
        px, py = out[-1]
        cx, cy = raw[i]
        nx, ny = raw[i + 1]
        if abs(nx - px) == 1 and abs(ny - py) == 1 and (
            (cx == px and cy == ny) or (cx == nx and cy == py)
        ):
            i += 1
            continue
        out.append((cx, cy))
        i += 1
    if out[-1] != raw[-1]:
        out.append(raw[-1])
    return out


def _trace_line(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """Return integer Bresenham coordinates from (x0, y0) to (x1, y1)."""
    pts: list[tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


def _draw_curve(
    canvas: Canvas,
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    color: RGBA,
    steps: int = 24,
    thickness: int = 1,
) -> None:
    """Draw a pixel-perfect L-corner-cleaned quadratic Bezier curve."""
    samples = _qbezier(p0, p1, p2, steps)
    raw: list[tuple[int, int]] = []
    for i in range(len(samples) - 1):
        seg = _trace_line(samples[i][0], samples[i][1], samples[i + 1][0], samples[i + 1][1])
        for pt in seg:
            if not raw or raw[-1] != pt:
                raw.append(pt)
    for px, py in _clean_1px_path(raw):
        canvas.set_pixel(px, py, color)
        if thickness > 1:
            canvas.set_pixel(px, py + 1, color)


def _draw_polyline(
    canvas: Canvas,
    pts: list[tuple[int, int]],
    color: RGBA,
    closed: bool = False,
) -> None:
    """Draw a clean 1px pixel path through ordered integer vertices."""
    if len(pts) < 2:
        return
    raw: list[tuple[int, int]] = []
    count = len(pts) if closed else len(pts) - 1
    for i in range(count):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        for pt in _trace_line(x0, y0, x1, y1):
            if not raw or raw[-1] != pt:
                raw.append(pt)
    for px, py in _clean_1px_path(raw):
        canvas.set_pixel(px, py, color)


def _draw_plane(
    canvas: Canvas,
    pts: list[tuple[int, int]],
    fill: RGBA,
    edge: RGBA | None = None,
) -> None:
    """Fill a polygon plane and optionally trace its perimeter with `edge`."""
    canvas.draw_polygon(pts, fill, filled=True)
    if edge is not None:
        _draw_polyline(canvas, pts, edge, closed=True)


def _draw_mistria_eye_v2(
    canvas: Canvas,
    cx: int,
    cy: int,
    is_near: bool,
    iris_col: RGBA,
    ink: RGBA,
    skin_d: RGBA,
    skin_dd: RGBA,
    facing_right: bool,
) -> None:
    """Render an authentic 90s-anime Mistria eye matching March/Balor pixel structure."""
    w = 9 if is_near else 7
    hw = w // 2
    white: RGBA = (255, 255, 255, 255)
    sclera_l: RGBA = (212, 208, 212, 255)
    sclera_d: RGBA = (165, 158, 164, 255)
    iris_d = darken(iris_col, 0.52)
    iris_l = brighten(iris_col, 1.32)
    pupil: RGBA = (20, 16, 22, 255)

    for dy in (-1, 0, 1):
        col = sclera_d if dy == -1 else (white if dy == 0 else sclera_l)
        for dx in range(-hw + 1, hw):
            canvas.set_pixel(cx + dx, cy + dy, col)
    canvas.set_pixel(cx - hw + 1, cy, white)
    canvas.set_pixel(cx + hw - 1, cy, sclera_l)

    gx = (1 if facing_right else -1) if is_near else 0
    ix = cx + gx
    for dx in (-1, 0, 1):
        canvas.set_pixel(ix + dx, cy - 1, iris_d)
        canvas.set_pixel(ix + dx, cy, iris_col)
        canvas.set_pixel(ix + dx, cy + 1, iris_l if dx == 0 else iris_col)
    canvas.set_pixel(ix, cy, pupil)
    canvas.set_pixel(ix, cy - 1, pupil)

    cl_x = ix - 1 if facing_right else ix + 1
    canvas.set_pixel(cl_x, cy - 1, white)
    canvas.set_pixel(cl_x, cy, white)

    for dx in range(-hw, hw + 1):
        canvas.set_pixel(cx + dx, cy - 2, ink)
    if is_near:
        wing_x = cx - hw - 1 if facing_right else cx + hw + 1
        canvas.set_pixel(wing_x, cy - 1, ink)
        for dx in range(-hw + 2, hw - 1):
            canvas.set_pixel(cx + dx, cy - 3, ink)
        canvas.set_pixel(cx - hw + 1, cy - 3, ink)
        canvas.set_pixel(cx + hw - 1, cy - 3, ink)
    else:
        for dx in range(-hw + 1, hw):
            canvas.set_pixel(cx + dx, cy - 3, ink)

    canvas.set_pixel(cx - hw, cy, skin_dd)
    canvas.set_pixel(cx + hw, cy, skin_dd)
    for dx in range(-hw + 2, hw - 1):
        canvas.set_pixel(cx + dx, cy + 2, skin_d)
    canvas.set_pixel(ix, cy + 2, skin_dd)


def _draw_head_and_neck(
    canvas: Canvas,
    sx: Any,
    sy: Any,
    c: dict[str, RGBA],
    facing_right: bool,
    preset: str,
    scar: bool,
) -> None:
    """Draw the Mistria 3/4 head, slender cylinder neck, ear, eyes, nose, and smirk."""
    ink = c["ink"]
    skin = c["skin"]
    skin_l = c["skin_l"]
    skin_d = c["skin_d"]
    skin_dd = c["skin_dd"]
    hair_d = c["hair_d"]

    # 1. Slender Mistria Neck (17px cylinder, x=47..64, y=49..67)
    neck_pts = [
        (sx(47), sy(48)),
        (sx(64), sy(48)),
        (sx(65), sy(61)),
        (sx(70), sy(67)),
        (sx(57), sy(74)),
        (sx(43), sy(66)),
        (sx(47), sy(59)),
    ]
    _draw_plane(canvas, neck_pts, skin)
    _draw_plane(
        canvas,
        [(sx(47), sy(48)), (sx(64), sy(48)), (sx(64), sy(56)), (sx(55), sy(59)), (sx(47), sy(55))],
        skin_d,
    )
    _draw_plane(
        canvas,
        [(sx(48), sy(50)), (sx(63), sy(50)), (sx(61), sy(54)), (sx(54), sy(55)), (sx(48), sy(53))],
        skin_dd,
    )
    _draw_polyline(canvas, [(sx(47), sy(52)), (sx(47), sy(60)), (sx(43), sy(65))], ink)
    _draw_polyline(canvas, [(sx(64), sy(52)), (sx(65), sy(61)), (sx(70), sy(66))], ink)
    _draw_curve(canvas, (sx(50), sy(59)), (sx(54), sy(65)), (sx(56), sy(70)), skin_d, 10)
    _draw_curve(canvas, (sx(63), sy(60)), (sx(60), sy(66)), (sx(58), sy(70)), skin_d, 10)
    _draw_curve(canvas, (sx(46), sy(65)), (sx(51), sy(68)), (sx(55), sy(70)), skin_dd, 10)
    _draw_curve(canvas, (sx(68), sy(65)), (sx(64), sy(68)), (sx(60), sy(70)), skin_dd, 10)

    # 2. Cranium & V-tapered 3/4 Jawline (x=40..72, y=16..53)
    head_outline = (
        _qbezier((sx(40), sy(32)), (sx(40), sy(16)), (sx(57), sy(16)), 10)
        + _qbezier((sx(57), sy(16)), (sx(72), sy(16)), (sx(72), sy(34)), 10)
        + _qbezier((sx(72), sy(34)), (sx(72), sy(45)), (sx(60), sy(53)), 10)
        + _qbezier((sx(60), sy(53)), (sx(49), sy(52)), (sx(41), sy(43)), 10)
        + [(sx(40), sy(37))]
    )
    _draw_plane(canvas, head_outline, skin)

    _draw_plane(
        canvas,
        [(sx(62), sy(51)), (sx(70), sy(44)), (sx(72), sy(34)), (sx(70), sy(26)), (sx(68), sy(39)), (sx(63), sy(48)), (sx(57), sy(51))],
        skin_d,
    )
    _draw_plane(
        canvas,
        [(sx(42), sy(42)), (sx(48), sy(49)), (sx(56), sy(51)), (sx(51), sy(49)), (sx(45), sy(43))],
        skin_d,
    )

    jaw_curve = (
        _qbezier((sx(41), sy(43)), (sx(49), sy(52)), (sx(60), sy(53)), 12)
        + _qbezier((sx(60), sy(53)), (sx(72), sy(45)), (sx(72), sy(32)), 12)
    )
    _draw_polyline(canvas, jaw_curve, ink)
    canvas.set_pixel(sx(59), sy(52), skin_dd)
    canvas.set_pixel(sx(61), sy(52), skin_dd)

    # 3. Exposed Mistria Ear (in front of back hair!)
    ear_pts = [(sx(35), sy(33)), (sx(38), sy(30)), (sx(41), sy(34)), (sx(41), sy(42)), (sx(36), sy(43)), (sx(35), sy(39))]
    _draw_plane(canvas, ear_pts, skin, edge=ink)
    _draw_curve(canvas, (sx(37), sy(33)), (sx(39), sy(36)), (sx(37), sy(40)), skin_dd, 8)
    canvas.set_pixel(sx(38), sy(37), skin_d)

    # 4. Eyes, Eyebrows, Nose, Mouth, Blush, Scar
    eye_y = sy(34)
    left_ex = sx(51)
    right_ex = sx(66)
    _draw_mistria_eye_v2(
        canvas, left_ex, eye_y, True, c["eye_color"], ink, skin_d, skin_dd, facing_right
    )
    _draw_mistria_eye_v2(
        canvas, right_ex, eye_y + 1, False, c["eye_color"], ink, skin_d, skin_dd, facing_right
    )

    brow_col = ink if preset == "samurai" else hair_d
    # 1px upper eyelid crease + sleek 90s-anime tapered eyebrows above lid
    _draw_polyline(canvas, [(left_ex - 4, eye_y - 3), (left_ex + 2, eye_y - 3)], skin_d)
    _draw_polyline(canvas, [(right_ex - 2, eye_y - 2), (right_ex + 2, eye_y - 2)], skin_d)
    _draw_curve(canvas, (left_ex - 5, eye_y - 5), (left_ex - 1, eye_y - 7), (left_ex + 4, eye_y - 5), brow_col, 10)
    _draw_polyline(canvas, [(left_ex - 2, eye_y - 6), (left_ex + 3, eye_y - 5)], brow_col)
    _draw_curve(canvas, (right_ex - 3, eye_y - 4), (right_ex + 1, eye_y - 6), (right_ex + 4, eye_y - 4), brow_col, 8)
    _draw_polyline(canvas, [(right_ex - 2, eye_y - 4), (right_ex + 1, eye_y - 5)], brow_col)

    for bx in (left_ex - 3, left_ex, right_ex + 1, right_ex + 3):
        canvas.set_pixel(bx, eye_y + 4, skin_d)
        canvas.set_pixel(bx - 1, eye_y + 5, skin_d)

    nx, ny = sx(61), sy(40)
    canvas.set_pixel(nx - 1, ny - 3, skin_d)
    canvas.set_pixel(nx, ny - 2, skin_d)
    canvas.set_pixel(nx + 1, ny - 1, skin_d)
    canvas.set_pixel(nx + 1, ny, skin_dd)
    canvas.set_pixel(nx, ny + 1, skin_dd)
    canvas.set_pixel(nx - 1, ny + 1, skin_d)
    canvas.set_pixel(nx, ny, skin_l)

    mx, my = sx(59), sy(46)
    if preset == "samurai":
        _draw_curve(canvas, (mx - 4, my), (mx, my + 1), (mx + 4, my - 1), skin_dd, 8)
        canvas.set_pixel(mx + 3, my - 1, ink)
        canvas.set_pixel(mx - 1, my + 2, skin_d)
        canvas.set_pixel(mx, my + 2, skin_d)
    else:
        _draw_curve(canvas, (mx - 4, my), (mx, my + 2), (mx + 5, my), skin_dd, 10)
        canvas.set_pixel(mx, my + 3, skin_d)
        canvas.set_pixel(mx + 1, my + 3, skin_d)

    if scar:
        _draw_polyline(canvas, [(sx(66), sy(28)), (sx(69), sy(31)), (sx(70), sy(39))], skin_dd)
        canvas.set_pixel(sx(67), sy(28), skin_l)
        canvas.set_pixel(sx(69), sy(38), skin_l)


def _draw_samurai_hair_back(
    canvas: Canvas,
    sx: Any,
    sy: Any,
    c: dict[str, RGBA],
) -> None:
    """Draw swept-back samurai nape & warrior locks BEHIND the head & visible ear."""
    ink = c["ink"]
    hair = c["hair"]
    hair_l = c["hair_l"]
    hair_d = c["hair_d"]

    # Organic inward-curling Balor/Olric nape locks behind visible ear
    back_left = (
        _qbezier((sx(34), sy(24)), (sx(27), sy(33)), (sx(28), sy(44)), 10)
        + _qbezier((sx(28), sy(44)), (sx(30), sy(51)), (sx(36), sy(53)), 8)
        + [(sx(38), sy(47)), (sx(41), sy(52)), (sx(45), sy(48)), (sx(44), sy(33))]
    )
    _draw_plane(canvas, back_left, hair_d, edge=ink)
    _draw_plane(
        canvas,
        _qbezier((sx(31), sy(30)), (sx(29), sy(39)), (sx(33), sy(46)), 8)
        + [(sx(36), sy(43)), (sx(36), sy(30))],
        hair,
    )
    _draw_curve(canvas, (sx(32), sy(30)), (sx(30), sy(37)), (sx(32), sy(44)), hair_l, 8)
    _draw_curve(canvas, (sx(36), sy(42)), (sx(37), sy(47)), (sx(40), sy(50)), hair, 6)
    _draw_curve(canvas, (sx(31), sy(35)), (sx(31), sy(44)), (sx(34), sy(51)), ink, 8)
    _draw_curve(canvas, (sx(35), sy(39)), (sx(35), sy(46)), (sx(38), sy(50)), ink, 8)

    # Small tapered lock on far right behind jaw
    _draw_plane(
        canvas,
        [(sx(70), sy(35)), (sx(76), sy(38)), (sx(74), sy(46)), (sx(68), sy(46))],
        hair_d,
        edge=ink,
    )


def _draw_samurai_hair_front(
    canvas: Canvas,
    sx: Any,
    sy: Any,
    c: dict[str, RGBA],
) -> None:
    """Draw sleek Mistria warrior hair crown, swept bangs, and chonmage ponytail topknot."""
    ink = c["ink"]
    hair = c["hair"]
    hair_l = c["hair_l"]
    hair_d = c["hair_d"]
    cord = c["accent"]

    # Warrior topknot / swept samurai tail (curved organic sweep, NOT a brick)
    tail_pts = (
        _qbezier((sx(42), sy(14)), (sx(34), sy(11)), (sx(28), sy(16)), 8)
        + _qbezier((sx(28), sy(16)), (sx(33), sy(19)), (sx(41), sy(17)), 8)
    )
    _draw_plane(canvas, tail_pts, hair_d, edge=ink)
    _draw_curve(canvas, (sx(41), sy(15)), (sx(35), sy(14)), (sx(29), sy(16)), ink, 6)
    knot_pts = (
        _qbezier((sx(42), sy(14)), (sx(45), sy(4)), (sx(55), sy(5)), 8)
        + _qbezier((sx(55), sy(5)), (sx(60), sy(7)), (sx(56), sy(14)), 8)
    )
    _draw_plane(canvas, knot_pts, hair, edge=ink)
    _draw_plane(canvas, [(sx(45), sy(8)), (sx(52), sy(6)), (sx(55), sy(9)), (sx(47), sy(11))], hair_l)
    # White/gold motoyui cord wrapping topknot base
    _draw_plane(canvas, [(sx(43), sy(12)), (sx(56), sy(11)), (sx(57), sy(14)), (sx(42), sy(15))], cord, edge=ink)

    # Swept-back cranium hair volume cleanly parting above visible ear
    crown_pts = (
        _qbezier((sx(34), sy(31)), (sx(33), sy(17)), (sx(48), sy(13)), 10)
        + _qbezier((sx(48), sy(13)), (sx(66), sy(12)), (sx(74), sy(26)), 10)
        + [(sx(73), sy(31)), (sx(69), sy(24)), (sx(58), sy(20)), (sx(46), sy(22)), (sx(39), sy(29)), (sx(36), sy(30))]
    )
    _draw_plane(canvas, crown_pts, hair, edge=ink)

    _draw_plane(
        canvas,
        [(sx(61), sy(15)), (sx(71), sy(19)), (sx(73), sy(27)), (sx(68), sy(24)), (sx(62), sy(19))],
        hair_d,
    )
    _draw_plane(
        canvas,
        [(sx(38), sy(21)), (sx(47), sy(15)), (sx(59), sy(15)), (sx(55), sy(18)), (sx(46), sy(19)), (sx(40), sy(24))],
        hair_l,
    )
    _draw_curve(canvas, (sx(40), sy(24)), (sx(50), sy(19)), (sx(62), sy(19)), hair_l, 12)

    # Tapered sideburn framing front of visible ear + loose anime forehead locks
    _draw_plane(canvas, [(sx(39), sy(25)), (sx(43), sy(22)), (sx(43), sy(32)), (sx(41), sy(36)), (sx(39), sy(30))], hair)
    _draw_polyline(canvas, [(sx(43), sy(23)), (sx(43), sy(32)), (sx(41), sy(36))], hair_d)

    # Sweeping Mistria forehead bangs (sharper tapered locks + specular highlights)
    _draw_plane(canvas, [(sx(51), sy(19)), (sx(58), sy(19)), (sx(54), sy(31)), (sx(50), sy(26))], hair)
    _draw_curve(canvas, (sx(53), sy(20)), (sx(53), sy(24)), (sx(53), sy(28)), hair_l, 6)
    _draw_polyline(canvas, [(sx(58), sy(20)), (sx(54), sy(31)), (sx(50), sy(26))], ink)
    _draw_plane(canvas, [(sx(63), sy(18)), (sx(71), sy(21)), (sx(74), sy(33)), (sx(68), sy(28)), (sx(64), sy(23))], hair)
    _draw_curve(canvas, (sx(65), sy(20)), (sx(69), sy(23)), (sx(71), sy(28)), hair_l, 6)
    _draw_polyline(canvas, [(sx(64), sy(23)), (sx(68), sy(28)), (sx(74), sy(33))], ink)


def _draw_samurai_hat_back(canvas: Canvas, sx: Any, sy: Any, c: dict[str, RGBA]) -> None:
    """Draw a conical woven kasa hat slung behind the samurai's shoulders."""
    ink = c["ink"]
    hat = c["hat"]
    hat_l = c["hat_l"]
    hat_d = c["hat_d"]
    _draw_plane(
        canvas,
        [(sx(16), sy(64)), (sx(58), sy(46)), (sx(99), sy(64)), (sx(90), sy(85)), (sx(25), sy(85))],
        hat,
        edge=ink,
    )
    _draw_plane(canvas, [(sx(23), sy(64)), (sx(58), sy(48)), (sx(62), sy(58)), (sx(29), sy(72))], hat_l)
    _draw_plane(canvas, [(sx(66), sy(54)), (sx(96), sy(64)), (sx(88), sy(81)), (sx(64), sy(76))], hat_d)
    for ry in (58, 66, 74):
        _draw_curve(canvas, (sx(25), sy(ry)), (sx(58), sy(ry - 6)), (sx(90), sy(ry)), hat_d, 16)


def _draw_samurai_body(
    canvas: Canvas,
    sx: Any,
    sy: Any,
    c: dict[str, RGBA],
    has_hat: bool,
    hat_mode: str,
) -> None:
    """Draw waist-up Mistria samurai torso with rounded shoulders, curved kote, katana, and obi."""
    ink = c["ink"]
    skin = c["skin"]
    skin_l = c["skin_l"]
    skin_d = c["skin_d"]
    skin_dd = c["skin_dd"]
    shirt = c["shirt"]
    shirt_d = c["shirt_d"]
    kimono = c["kimono"]
    kimono_l = c["kimono_l"]
    kimono_d = c["kimono_d"]
    haori = c["garment"]
    haori_l = c["garment_l"]
    haori_d = c["garment_d"]
    gold = c["accent"]
    gold_d = darken(gold, 0.70)
    gold_l = brighten(gold, 1.25)
    hakama = c["hakama"]
    hakama_d = c["hakama_d"]

    if has_hat and hat_mode == "back":
        _draw_samurai_hat_back(canvas, sx, sy, c)

    # 1. Pleated Hakama running flush to bottom y=159
    _draw_plane(canvas, [(sx(26), sy(121)), (sx(88), sy(121)), (sx(94), sy(159)), (sx(21), sy(159))], hakama)
    _draw_polyline(canvas, [(sx(26), sy(121)), (sx(21), sy(159))], ink)
    _draw_polyline(canvas, [(sx(88), sy(121)), (sx(94), sy(159))], ink)
    for px_top, px_bot in ((35, 30), (48, 45), (61, 61), (75, 80)):
        _draw_plane(
            canvas,
            [(sx(px_top), sy(123)), (sx(px_top + 4), sy(123)), (sx(px_bot + 4), sy(159)), (sx(px_bot - 1), sy(159))],
            hakama_d,
        )
        _draw_polyline(canvas, [(sx(px_top), sy(123)), (sx(px_bot), sy(159))], ink)

    # 2. Inner Juban White Collar + Cross-Wrapped Indigo Kosode hugging neck smoothly
    _draw_plane(canvas, [(sx(34), sy(66)), (sx(78), sy(66)), (sx(86), sy(121)), (sx(27), sy(121))], kimono)
    _draw_plane(
        canvas,
        [(sx(43), sy(62)), (sx(48), sy(62)), (sx(58), sy(76)), (sx(66), sy(62)), (sx(70), sy(64)), (sx(58), sy(82)), (sx(42), sy(65))],
        shirt,
    )
    _draw_plane(
        canvas,
        [(sx(65), sy(63)), (sx(70), sy(64)), (sx(58), sy(82)), (sx(57), sy(77))],
        shirt_d,
    )
    _draw_polyline(canvas, [(sx(43), sy(62)), (sx(58), sy(82)), (sx(70), sy(64))], ink)

    _draw_plane(
        canvas,
        [(sx(38), sy(64)), (sx(44), sy(62)), (sx(61), sy(85)), (sx(64), sy(115)), (sx(51), sy(115)), (sx(42), sy(88))],
        kimono_l,
    )
    _draw_plane(
        canvas,
        [(sx(62), sy(79)), (sx(73), sy(64)), (sx(82), sy(92)), (sx(83), sy(118)), (sx(61), sy(118))],
        kimono_d,
    )
    _draw_polyline(canvas, [(sx(44), sy(63)), (sx(61), sy(86)), (sx(63), sy(114))], ink)
    _draw_polyline(canvas, [(sx(72), sy(64)), (sx(59), sy(82))], ink)
    _draw_curve(canvas, (sx(45), sy(94)), (sx(52), sy(101)), (sx(56), sy(109)), kimono_d, 10)
    _draw_curve(canvas, (sx(66), sy(94)), (sx(72), sy(101)), (sx(74), sy(109)), kimono_d, 10)

    # 3. Broad, Smoothly Rounded Haori / Jinbaori Over-Coat (draped flush around trapezius collar)
    left_sh = _qbezier((sx(17), sy(102)), (sx(19), sy(67)), (sx(42), sy(62)), 14)
    haori_l_pts = left_sh + [(sx(45), sy(63)), (sx(41), sy(96)), (sx(35), sy(128)), (sx(22), sy(125))]
    _draw_plane(canvas, haori_l_pts, haori)
    _draw_polyline(canvas, left_sh + [(sx(45), sy(63)), (sx(41), sy(96)), (sx(35), sy(128))], ink)
    _draw_plane(
        canvas,
        _qbezier((sx(21), sy(85)), (sx(22), sy(67)), (sx(41), sy(63)), 10)
        + [(sx(41), sy(71)), (sx(34), sy(84)), (sx(23), sy(92))],
        haori_l,
    )

    right_sh = _qbezier((sx(71), sy(62)), (sx(94), sy(67)), (sx(101), sy(94)), 14)
    haori_r_pts = [(sx(69), sy(63))] + right_sh + [(sx(93), sy(122)), (sx(80), sy(122)), (sx(76), sy(95))]
    _draw_plane(canvas, haori_r_pts, haori)
    _draw_polyline(canvas, [(sx(69), sy(63))] + right_sh, ink)
    # Shadow only along outer armpit/side drape (keeping chest crimson bright like Mistria!)
    _draw_plane(
        canvas,
        [(sx(84), sy(69)), (sx(96), sy(78)), (sx(96), sy(108)), (sx(83), sy(118)), (sx(83), sy(92))],
        haori_d,
    )
    _draw_polyline(canvas, [(sx(44), sy(63)), (sx(40), sy(94)), (sx(35), sy(124))], haori_d)
    _draw_polyline(canvas, [(sx(71), sy(63)), (sx(75), sy(94)), (sx(79), sy(121))], haori_d)
    for mx_c, my_c in ((sx(36), sy(83)), (sx(80), sy(83))):
        _draw_plane(canvas, [(mx_c, my_c - 3), (mx_c + 3, my_c), (mx_c, my_c + 3), (mx_c - 3, my_c)], gold)
        canvas.set_pixel(mx_c, my_c, haori_d)
        canvas.set_pixel(mx_c, my_c - 2, gold_l)
    _draw_curve(canvas, (sx(24), sy(85)), (sx(31), sy(93)), (sx(34), sy(103)), haori_d, 10)
    _draw_curve(canvas, (sx(84), sy(76)), (sx(89), sy(89)), (sx(88), sy(102)), haori_d, 10)

    # 4. Bold Clean Obi Sash + Single Obijime Cord + Folded Crimson Knot (y=112..126)
    obi_pts = (
        _qbezier((sx(28), sy(113)), (sx(58), sy(116)), (sx(87), sy(113)), 10)
        + _qbezier((sx(87), sy(124)), (sx(58), sy(127)), (sx(27), sy(124)), 10)[::-1]
    )
    _draw_plane(canvas, obi_pts, kimono_d, edge=ink)
    _draw_plane(
        canvas,
        _qbezier((sx(30), sy(114)), (sx(58), sy(117)), (sx(85), sy(114)), 10)
        + _qbezier((sx(85), sy(118)), (sx(58), sy(121)), (sx(30), sy(118)), 10)[::-1],
        kimono,
    )
    _draw_curve(canvas, (sx(29), sy(119)), (sx(58), sy(122)), (sx(86), sy(119)), gold, 14, thickness=2)
    _draw_curve(canvas, (sx(30), sy(119)), (sx(58), sy(122)), (sx(85), sy(119)), gold_l, 14)
    # Sculpted crimson obi knot with upper highlight & tucked shadow lip
    _draw_plane(
        canvas,
        [(sx(59), sy(113)), (sx(70), sy(112)), (sx(72), sy(120)), (sx(69), sy(126)), (sx(59), sy(126)), (sx(57), sy(119))],
        haori,
        edge=ink,
    )
    _draw_plane(canvas, [(sx(60), sy(113)), (sx(69), sy(113)), (sx(68), sy(116)), (sx(60), sy(117))], haori_l)
    _draw_plane(canvas, [(sx(59), sy(121)), (sx(70), sy(121)), (sx(69), sy(125)), (sx(59), sy(125))], haori_d)
    _draw_curve(canvas, (sx(60), sy(118)), (sx(64), sy(120)), (sx(69), sy(118)), haori_d, 6)

    # 5. Viewer's Right Arm: Smooth Pinch-Free Elbow -> Kote Bracer -> Mistria Hand on Hip
    r_sleeve = (
        _qbezier((sx(92), sy(78)), (sx(109), sy(89)), (sx(112), sy(108)), 12)
        + [(sx(100), sy(112)), (sx(92), sy(100))]
    )
    _draw_plane(canvas, r_sleeve, kimono, edge=ink)
    _draw_plane(canvas, [(sx(96), sy(88)), (sx(108), sy(98)), (sx(106), sy(109)), (sx(96), sy(101))], kimono_d)
    _draw_curve(canvas, (sx(94), sy(90)), (sx(100), sy(99)), (sx(102), sy(107)), kimono_d, 8)
    # Seamless continuous outer silhouette from elbow (111,108) -> wrist (90,127)
    r_forearm = (
        _qbezier((sx(110), sy(106)), (sx(114), sy(115)), (sx(103), sy(125)), 12)
        + [(sx(90), sy(128)), (sx(90), sy(117)), (sx(100), sy(108))]
    )
    _draw_plane(canvas, r_forearm, hakama, edge=ink)
    _draw_plane(canvas, [(sx(95), sy(115)), (sx(105), sy(115)), (sx(101), sy(123)), (sx(93), sy(122))], gold)
    _draw_polyline(canvas, [(sx(96), sy(115)), (sx(105), sy(115))], gold_l)
    _draw_curve(canvas, (sx(94), sy(119)), (sx(99), sy(120)), (sx(103), sy(119)), haori_l, 8)
    # Graceful Mistria Right Hand resting along obi/hip (angled taper + knuckle highlight)
    _draw_plane(
        canvas,
        [(sx(79), sy(116)), (sx(87), sy(115)), (sx(92), sy(119)), (sx(90), sy(126)), (sx(82), sy(127)), (sx(77), sy(121))],
        skin,
        edge=ink,
    )
    _draw_polyline(canvas, [(sx(80), sy(119)), (sx(85), sy(120))], skin_dd)
    _draw_polyline(canvas, [(sx(80), sy(122)), (sx(86), sy(123))], skin_dd)
    _draw_polyline(canvas, [(sx(82), sy(124)), (sx(87), sy(125))], skin_dd)
    canvas.set_pixel(sx(87), sy(118), skin_l)

    # 6. Viewer's Left Arm + Curved Katana Scabbard + Unobstructed Tsuka Hilt & Gold Tsuba
    # Left kimono sleeve tucked neatly behind sword hilt
    l_sleeve = (
        _qbezier((sx(18), sy(84)), (sx(12), sy(98)), (sx(14), sy(114)), 10)
        + [(sx(23), sy(114)), (sx(26), sy(96))]
    )
    _draw_plane(canvas, l_sleeve, kimono, edge=ink)
    _draw_plane(canvas, [(sx(14), sy(108)), (sx(23), sy(108)), (sx(24), sy(117)), (sx(16), sy(117))], hakama, edge=ink)
    _draw_plane(canvas, [(sx(16), sy(110)), (sx(22), sy(110)), (sx(22), sy(114)), (sx(16), sy(114))], gold)

    # Curved Lacquered Katana Scabbard (Saya) sweeping gracefully across waist
    saya_top = _qbezier((sx(31), sy(117)), (sx(58), sy(126)), (sx(89), sy(133)), 14)
    saya_bot = _qbezier((sx(88), sy(138)), (sx(57), sy(131)), (sx(28), sy(121)), 14)
    _draw_plane(canvas, saya_top + saya_bot, hakama_d, edge=ink)
    _draw_curve(canvas, (sx(34), sy(120)), (sx(58), sy(128)), (sx(86), sy(135)), haori_l, 14)

    # Unobstructed Katana Tsuka Hilt angling cleanly forward-left (x=8..31, y=94..118)
    _draw_plane(
        canvas,
        [(sx(8), sy(98)), (sx(12), sy(94)), (sx(30), sy(112)), (sx(26), sy(116))],
        haori_d,
        edge=ink,
    )
    # Crisp diamond tsuka-ito wrap visible along the upper hilt!
    for step in range(4):
        hx = sx(11 + step * 3)
        hy = sy(98 + step * 3)
        canvas.set_pixel(hx, hy, gold_l)
        canvas.set_pixel(hx + 1, hy, shirt)
    _draw_plane(canvas, [(sx(7), sy(95)), (sx(11), sy(92)), (sx(13), sy(95)), (sx(9), sy(98))], gold, edge=ink)

    # Ornate circular Gold Tsuba handguard
    _draw_plane(
        canvas,
        [(sx(27), sy(109)), (sx(33), sy(110)), (sx(34), sy(117)), (sx(29), sy(121)), (sx(24), sy(116))],
        gold,
        edge=ink,
    )
    canvas.set_pixel(sx(29), sy(112), gold_l)
    canvas.set_pixel(sx(30), sy(117), gold_d)

    # Articulated Left Hand resting casually over lower hilt / tsuba
    _draw_plane(
        canvas,
        [(sx(19), sy(110)), (sx(26), sy(110)), (sx(28), sy(116)), (sx(24), sy(121)), (sx(17), sy(117))],
        skin,
        edge=ink,
    )
    for fx, fy in ((22, 113), (24, 115), (24, 118)):
        _draw_polyline(canvas, [(sx(fx - 2), sy(fy)), (sx(fx + 1), sy(fy + 1))], skin_dd)
    canvas.set_pixel(sx(21), sy(112), skin_l)

    if has_hat and hat_mode == "back":
        _draw_curve(canvas, (sx(42), sy(63)), (sx(58), sy(73)), (sx(72), sy(64)), haori_l, 14)
        _draw_curve(canvas, (sx(56), sy(70)), (sx(58), sy(79)), (sx(57), sy(85)), haori_d, 8)
    elif has_hat and hat_mode == "worn":
        _draw_plane(
            canvas,
            [(sx(14), sy(23)), (sx(58), sy(5)), (sx(102), sy(23)), (sx(94), sy(27)), (sx(20), sy(27))],
            c["hat"],
            edge=ink,
        )
        _draw_plane(canvas, [(sx(21), sy(22)), (sx(58), sy(7)), (sx(60), sy(17)), (sx(27), sy(23))], c["hat_l"])
        _draw_plane(canvas, [(sx(62), sy(11)), (sx(98), sy(23)), (sx(90), sy(25)), (sx(62), sy(20))], c["hat_d"])
        _draw_curve(canvas, (sx(41), sy(36)), (sx(58), sy(58)), (sx(72), sy(34)), haori_l, 16)


def _draw_farmer_hair_and_body(
    canvas: Canvas,
    sx: Any,
    sy: Any,
    c: dict[str, RGBA],
    has_hat: bool,
    has_beard: bool,
    gesture: str,
) -> None:
    """Draw upgraded waist-up Mistria farmer with organic curved arms & waving hand."""
    ink = c["ink"]
    skin = c["skin"]
    skin_l = c["skin_l"]
    skin_d = c["skin_d"]
    skin_dd = c["skin_dd"]
    hair = c["hair"]
    hair_l = c["hair_l"]
    shirt = c["shirt"]
    shirt_d = c["shirt_d"]
    garment = c["garment"]
    garment_l = c["garment_l"]
    garment_d = c["garment_d"]
    gold = c["accent"]

    _draw_plane(
        canvas,
        [(sx(31), sy(34)), (sx(32), sy(17)), (sx(50), sy(12)), (sx(71), sy(14)), (sx(75), sy(28)), (sx(70), sy(24)), (sx(58), sy(21)), (sx(42), sy(25))],
        hair,
        edge=ink,
    )
    _draw_plane(canvas, [(sx(37), sy(21)), (sx(49), sy(15)), (sx(62), sy(16)), (sx(50), sy(20))], hair_l)

    if has_hat:
        _draw_plane(canvas, [(sx(37), sy(20)), (sx(44), sy(6)), (sx(68), sy(6)), (sx(75), sy(20))], c["hat"], edge=ink)
        _draw_plane(canvas, [(sx(43), sy(15)), (sx(48), sy(8)), (sx(61), sy(9)), (sx(52), sy(16))], c["hat_l"])
        _draw_plane(canvas, [(sx(37), sy(16)), (sx(75), sy(16)), (sx(76), sy(20)), (sx(36), sy(20))], garment, edge=ink)
        _draw_plane(canvas, [(sx(18), sy(22)), (sx(58), sy(14)), (sx(96), sy(22)), (sx(58), sy(28))], c["hat"], edge=ink)
        _draw_curve(canvas, (sx(24), sy(22)), (sx(58), sy(17)), (sx(90), sy(22)), c["hat_l"], 18)

    # Organic Mistria forearm silhouette curving slightly outward & flush at bottom y=159
    forearm_l = _qbezier((sx(18), sy(108)), (sx(14), sy(128)), (sx(21), sy(159)), 10)
    forearm_r = _qbezier((sx(30), sy(159)), (sx(31), sy(131)), (sx(31), sy(108)), 10)
    _draw_plane(canvas, forearm_l + [(sx(30), sy(159))] + forearm_r, skin)
    _draw_polyline(canvas, forearm_l, ink)
    _draw_polyline(canvas, forearm_r, ink)
    _draw_plane(
        canvas,
        _qbezier((sx(27), sy(112)), (sx(29), sy(132)), (sx(28), sy(158)), 8)
        + [(sx(30), sy(158)), (sx(31), sy(112))],
        skin_d,
    )
    _draw_curve(canvas, (sx(20), sy(118)), (sx(19), sy(134)), (sx(23), sy(150)), skin_l, 10)

    if gesture == "wave":
        wave_arm = (
            [(sx(88), sy(96))]
            + _qbezier((sx(88), sy(96)), (sx(103), sy(107)), (sx(110), sy(96)), 8)
            + _qbezier((sx(110), sy(96)), (sx(115), sy(84)), (sx(114), sy(72)), 8)
            + [(sx(107), sy(72))]
            + _qbezier((sx(107), sy(72)), (sx(105), sy(86)), (sx(97), sy(92)), 8)
            + [(sx(90), sy(82))]
        )
        _draw_plane(canvas, wave_arm, skin, edge=ink)
        _draw_curve(canvas, (sx(98), sy(97)), (sx(104), sy(99)), (sx(108), sy(92)), skin_d, 8)
        # Hayden_spring.png style tall tapered open waving hand with staggered diagonal fingertips
        palm_pts = [
            (sx(105), sy(73)),
            (sx(103), sy(64)),
            (sx(105), sy(54)),
            (sx(107), sy(54)),
            (sx(109), sy(52)),
            (sx(111), sy(52)),
            (sx(113), sy(54)),
            (sx(115), sy(56)),
            (sx(117), sy(59)),
            (sx(114), sy(72)),
        ]
        _draw_plane(canvas, palm_pts, skin, edge=ink)
        _draw_plane(
            canvas,
            [(sx(99), sy(65)), (sx(101), sy(59)), (sx(104), sy(61)), (sx(106), sy(70)), (sx(102), sy(71))],
            skin,
            edge=ink,
        )
        _draw_polyline(canvas, [(sx(108), sy(54)), (sx(107), sy(63))], skin_dd)
        _draw_polyline(canvas, [(sx(112), sy(53)), (sx(110), sy(63))], skin_dd)
        _draw_polyline(canvas, [(sx(115), sy(56)), (sx(113), sy(64))], skin_dd)
        _draw_curve(canvas, (sx(105), sy(64)), (sx(109), sy(67)), (sx(108), sy(71)), skin_d, 6)
    else:
        _draw_plane(
            canvas,
            _qbezier((sx(84), sy(108)), (sx(83), sy(132)), (sx(85), sy(159)), 8)
            + [(sx(97), sy(159))]
            + _qbezier((sx(97), sy(159)), (sx(100), sy(130)), (sx(96), sy(108)), 8),
            skin,
            edge=ink,
        )

    sh_l = _qbezier((sx(18), sy(108)), (sx(19), sy(72)), (sx(42), sy(63)), 12)
    sh_r = _qbezier((sx(74), sy(63)), (sx(94), sy(71)), (sx(97), sy(105)), 12)
    _draw_plane(canvas, sh_l + sh_r + [(sx(84), sy(108)), (sx(31), sy(108))], shirt, edge=ink)
    _draw_plane(canvas, [(sx(17), sy(106)), (sx(33), sy(106)), (sx(32), sy(112)), (sx(18), sy(112))], shirt_d, edge=ink)
    if gesture != "wave":
        _draw_plane(canvas, [(sx(83), sy(106)), (sx(98), sy(106)), (sx(97), sy(112)), (sx(84), sy(112))], shirt_d, edge=ink)

    _draw_plane(canvas, [(sx(39), sy(63)), (sx(46), sy(62)), (sx(52), sy(72)), (sx(41), sy(72))], shirt, edge=ink)
    _draw_plane(canvas, [(sx(74), sy(63)), (sx(67), sy(62)), (sx(62), sy(72)), (sx(73), sy(72))], shirt, edge=ink)
    _draw_curve(canvas, (sx(48), sy(69)), (sx(58), sy(74)), (sx(68), sy(69)), shirt_d, 10)
    _draw_curve(canvas, (sx(23), sy(84)), (sx(27), sy(96)), (sx(25), sy(104)), shirt_d, 10)
    _draw_curve(canvas, (sx(87), sy(82)), (sx(91), sy(92)), (sx(90), sy(100)), shirt_d, 10)

    _draw_plane(
        canvas,
        [(sx(31), sy(159)), (sx(34), sy(94)), (sx(41), sy(65)), (sx(48), sy(65)), (sx(50), sy(88)), (sx(66), sy(88)), (sx(68), sy(65)), (sx(75), sy(65)), (sx(82), sy(94)), (sx(85), sy(159))],
        garment,
    )
    _draw_plane(canvas, [(sx(74), sy(86)), (sx(81), sy(96)), (sx(84), sy(158)), (sx(76), sy(158))], garment_d)
    _draw_polyline(canvas, [(sx(42), sy(66)), (sx(44), sy(86))], garment_l)
    _draw_polyline(canvas, [(sx(69), sy(66)), (sx(68), sy(86))], garment_l)
    _draw_polyline(canvas, [(sx(31), sy(159)), (sx(34), sy(94)), (sx(41), sy(65)), (sx(48), sy(65)), (sx(50), sy(88)), (sx(66), sy(88)), (sx(68), sy(65)), (sx(75), sy(65)), (sx(82), sy(94)), (sx(85), sy(159))], ink)
    # Mistria shaded bib pocket with 2px fold lip + sel-out seams
    _draw_plane(canvas, [(sx(49), sy(98)), (sx(67), sy(98)), (sx(67), sy(114)), (sx(63), sy(118)), (sx(53), sy(118)), (sx(49), sy(114))], garment_d, edge=ink)
    _draw_plane(canvas, [(sx(50), sy(99)), (sx(66), sy(99)), (sx(66), sy(102)), (sx(50), sy(102))], garment)
    _draw_polyline(canvas, [(sx(51), sy(102)), (sx(65), sy(102))], garment_l)
    _draw_curve(canvas, (sx(36), sy(122)), (sx(48), sy(126)), (sx(62), sy(124)), garment_d, 12)
    _draw_plane(canvas, [(sx(41), sy(86)), (sx(49), sy(86)), (sx(49), sy(91)), (sx(41), sy(91))], gold, edge=ink)
    _draw_plane(canvas, [(sx(67), sy(86)), (sx(75), sy(86)), (sx(75), sy(91)), (sx(67), sy(91))], gold, edge=ink)


def _draw_farmer_hair_only(
    canvas: Canvas,
    sx: Any,
    sy: Any,
    c: dict[str, RGBA],
    has_hat: bool,
    has_beard: bool,
) -> None:
    """Re-apply foreground farmer bangs, beard, and hat brim over head."""
    ink = c["ink"]
    hair = c["hair"]
    hair_l = c["hair_l"]
    hair_d = c["hair_d"]
    if has_beard:
        _draw_plane(
            canvas,
            [(sx(41), sy(43)), (sx(49), sy(50)), (sx(59), sy(51)), (sx(69), sy(46)), (sx(72), sy(41)), (sx(70), sy(49)), (sx(59), sy(54)), (sx(46), sy(51))],
            c["beard"],
            edge=ink,
        )
        # Cheek stubble transition dots like Hayden_spring.png
        canvas.set_pixel(sx(43), sy(42), hair_l)
        canvas.set_pixel(sx(45), sy(45), hair_l)
        canvas.set_pixel(sx(69), sy(42), hair_l)
    _draw_plane(
        canvas,
        [(sx(36), sy(26)), (sx(44), sy(17)), (sx(66), sy(17)), (sx(72), sy(27)), (sx(65), sy(23)), (sx(57), sy(28)), (sx(49), sy(22)), (sx(41), sy(29))],
        hair,
    )
    _draw_polyline(canvas, [(sx(41), sy(29)), (sx(49), sy(22)), (sx(57), sy(28)), (sx(65), sy(23)), (sx(72), sy(27))], hair_d)
    _draw_curve(canvas, (sx(42), sy(20)), (sx(53), sy(16)), (sx(66), sy(19)), hair_l, 12)
    if has_hat:
        _draw_plane(canvas, [(sx(18), sy(22)), (sx(58), sy(14)), (sx(96), sy(22)), (sx(58), sy(28))], c["hat"], edge=ink)
        _draw_curve(canvas, (sx(24), sy(22)), (sx(58), sy(17)), (sx(90), sy(22)), c["hat_l"], 18)
        _draw_curve(canvas, (sx(22), sy(24)), (sx(58), sy(21)), (sx(92), sy(24)), c["hat_d"], 18)


def draw_mistria_portrait(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any],
) -> None:
    """Draw a Fields of Mistria style waist-up portrait ('samurai' or 'farmer')."""
    w = max(96, int(op.get("width", 120)))
    h = max(128, int(op.get("height", 160)))
    scale = min(w / 120.0, h / 160.0)

    def p(name: str, fallback: str) -> RGBA:
        return parse_color(op.get(name, fallback), palette)

    preset = str(op.get("preset", op.get("archetype", "farmer"))).lower()
    is_samurai = preset == "samurai"

    ink = p("ink", "#000000" if is_samurai else "#181016")
    c: dict[str, RGBA] = {
        "ink": ink,
        "skin": p("skin", "#f5cfa0" if is_samurai else "#f2c18e"),
        "skin_l": p("skin_l", "#ffe7c2" if is_samurai else "#ffdfa8"),
        "skin_d": p("skin_d", "#cf916c" if is_samurai else "#c67d63"),
        "skin_dd": p("skin_dd", "#9c5c43"),
        "hair": p("hair", "#252b36" if is_samurai else "#6d4034"),
        "hair_l": p("hair_l", "#425367" if is_samurai else "#965b45"),
        "hair_d": p("hair_d", "#141621" if is_samurai else "#42242c"),
        "shirt": p("shirt", "#f2ebe4" if is_samurai else "#e5ead9"),
        "shirt_d": p("shirt_d", "#c7bdb8" if is_samurai else "#b5c2a8"),
        "kimono": p("kimono", "#353a50"),
        "kimono_l": p("kimono_l", "#4b5d73"),
        "kimono_d": p("kimono_d", "#222638"),
        "garment": p("garment", "#a83747" if is_samurai else "#5b483a"),
        "garment_l": p("garment_l", "#d35362" if is_samurai else "#7a6150"),
        "garment_d": p("garment_d", "#6e2130" if is_samurai else "#3d2f28"),
        "hakama": p("hakama", "#1f2230"),
        "hakama_d": p("hakama_d", "#131520"),
        "accent": p("accent", "#dca966"),
        "beard": p("beard_color", "#4a2b2b"),
        "eye_color": p("eye_color", "#6e4234" if is_samurai else "#4a7548"),
        "hat": p("hat_color", "#dcb05a"),
        "hat_l": p("hat_light", "#f7dc8c"),
        "hat_d": p("hat_dark", "#a67536"),
    }
    if c["eye_color"] == ink or sum(c["eye_color"][:3]) < 75:
        c["eye_color"] = (110, 66, 52, 255) if is_samurai else (74, 117, 72, 255)

    face_dir = str(op.get("face_dir", "three_quarter_right")).lower()
    facing_right = face_dir in ("right", "three_quarter_right", "3q_right")

    def sx(v: float) -> int:
        lx = v if facing_right else (120.0 - v)
        return max(0, min(canvas.width - 1, x + round(lx * scale)))

    def sy(v: float) -> int:
        return max(0, min(canvas.height - 1, y + round(v * scale)))

    if op.get("fill_background", False):
        prev_no = canvas.mark_no_outline
        canvas.mark_no_outline = True
        canvas.draw_rect(x, y, round(w), round(h), p("background", "#d6e6cf"), filled=True)
        canvas.mark_no_outline = prev_no

    has_hat = bool(op.get("hat", False))
    hat_mode = str(op.get("hat_mode", "back")).lower()

    if is_samurai:
        _draw_samurai_body(canvas, sx, sy, c, has_hat, hat_mode)
        _draw_samurai_hair_back(canvas, sx, sy, c)
        _draw_head_and_neck(canvas, sx, sy, c, facing_right, "samurai", bool(op.get("scar", True)))
        _draw_samurai_hair_front(canvas, sx, sy, c)
        if has_hat and hat_mode == "worn":
            _draw_plane(
                canvas,
                [(sx(14), sy(23)), (sx(58), sy(5)), (sx(102), sy(23)), (sx(94), sy(27)), (sx(20), sy(27))],
                c["hat"],
                edge=ink,
            )
            _draw_plane(canvas, [(sx(21), sy(22)), (sx(58), sy(7)), (sx(60), sy(17)), (sx(27), sy(23))], c["hat_l"])
            _draw_plane(canvas, [(sx(62), sy(11)), (sx(98), sy(23)), (sx(90), sy(25)), (sx(62), sy(20))], c["hat_d"])
    else:
        has_beard = bool(op.get("beard", False))
        _draw_farmer_hair_and_body(
            canvas,
            sx,
            sy,
            c,
            has_hat,
            has_beard,
            str(op.get("gesture", "idle")).lower(),
        )
        _draw_head_and_neck(canvas, sx, sy, c, facing_right, "farmer", False)
        _draw_farmer_hair_only(canvas, sx, sy, c, has_hat, has_beard)

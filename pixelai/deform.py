"""Spine deformation (bend/wave) and 2-bone analytical inverse kinematics (IK)."""

from __future__ import annotations

import math
from typing import Sequence

from pixelai.canvas import Canvas
from pixelai.color import RGBA, TRANSPARENT, brighten, darken
from pixelai.organic import draw_solid

Point2D = tuple[float, float]


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else (hi if v > hi else v)


def _seg_dist2(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    u = _clamp(((px - ax) * dx + (py - ay) * dy) / l2) if l2 > 1e-9 else 0.0
    qx = ax + dx * u - px
    qy = ay + dy * u - py
    return qx * qx + qy * qy


def solve_ik_2bone(
    hx: float,
    hy: float,
    fx: float,
    fy: float,
    l1: float,
    l2: float,
    direction: int = 1,
) -> Point2D:
    """Solve 2-bone analytical IK and return the joint position `(jx, jy)`.

    `direction` (+1 or -1) selects which side the elbow/knee bends toward.
    """
    l1 = max(1e-4, float(l1))
    l2 = max(1e-4, float(l2))
    d = math.hypot(fx - hx, fy - hy)
    base = math.atan2(fy - hy, fx - hx)
    d = max(abs(l1 - l2) + 1e-4, min(d, l1 + l2 - 1e-3))
    cos_a = _clamp((l1 * l1 + d * d - l2 * l2) / (2.0 * l1 * d), -1.0, 1.0)
    a = math.acos(cos_a)
    sign = 1.0 if direction >= 0 else -1.0
    ang = base - sign * a
    return (hx + math.cos(ang) * l1, hy + math.sin(ang) * l1)


def wave_polyline(
    points: Sequence[Sequence[float]],
    t: float = 0.0,
    amp: float = 3.0,
    wavelength: float = 16.0,
    anchor_from: float = 0.0,
) -> list[Point2D]:
    """Displace a spine polyline perpendicularly with a traveling sine wave."""
    pts = [(float(p[0]), float(p[1])) for p in points]
    n = len(pts)
    if n < 2:
        return pts
    s = [0.0]
    for i in range(1, n):
        s.append(s[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    total_len = s[-1] or 1.0
    wl = max(1e-4, float(wavelength))
    denom = max(1e-4, 1.0 - anchor_from)
    out: list[Point2D] = []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        seg_l = math.hypot(dx, dy) or 1.0
        k = _clamp((s[i] / total_len - anchor_from) / denom)
        off = amp * k * math.sin(math.pi * 2.0 * (s[i] / wl - t))
        out.append((p[0] - (dy / seg_l) * off, p[1] + (dx / seg_l) * off))
    return out


def build_strip(
    points: Sequence[Point2D], radius: float
) -> list[tuple[Point2D, Point2D]]:
    """Build left/right offset quad strip vertices along a polyline."""
    pts = [(float(p[0]), float(p[1])) for p in points]
    n = len(pts)
    if n < 2:
        raise ValueError("Spine polyline requires at least 2 points")
    dirs: list[Point2D] = []
    for i in range(n - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        l = math.hypot(dx, dy) or 1.0
        dirs.append((dx / l, dy / l))
    head = (pts[0][0] - dirs[0][0] * radius, pts[0][1] - dirs[0][1] * radius)
    tail = (pts[-1][0] + dirs[-1][0] * radius, pts[-1][1] + dirs[-1][1] * radius)
    p2 = [head, *pts, tail]
    d2 = [dirs[0], *dirs, dirs[-1]]
    normals: list[Point2D] = []
    for i in range(len(p2)):
        a = d2[max(0, i - 1)]
        b = d2[min(len(d2) - 1, i)]
        nx = -(a[1] + b[1])
        ny = a[0] + b[0]
        l = math.hypot(nx, ny) or 1.0
        nx /= l
        ny /= l
        miter = min(2.0, 1.0 / max(0.5, nx * -b[1] + ny * b[0]))
        normals.append((nx * miter * radius, ny * miter * radius))
    return [
        ((p[0] - nrm[0], p[1] - nrm[1]), (p[0] + nrm[0], p[1] + nrm[1]))
        for p, nrm in zip(p2, normals)
    ]


def inv_bilinear(
    px: float, py: float, a: Point2D, b: Point2D, c: Point2D, d: Point2D
) -> Point2D | None:
    """Invert bilinear interpolation inside quad (a, b, c, d) -> (u, v)."""
    ex, ey = b[0] - a[0], b[1] - a[1]
    fx, fy = d[0] - a[0], d[1] - a[1]
    gx = a[0] - b[0] + c[0] - d[0]
    gy = a[1] - b[1] + c[1] - d[1]
    hx, hy = px - a[0], py - a[1]

    k2 = gx * fy - gy * fx
    k1 = ex * fy - ey * fx + hx * gy - hy * gx
    k0 = hx * ey - hy * ex

    def _u_of(v: float) -> float:
        dx = ex + gx * v
        dy = ey + gy * v
        if abs(dx) > abs(dy):
            return (hx - fx * v) / dx if abs(dx) > 1e-12 else -1.0
        return (hy - fy * v) / dy if abs(dy) > 1e-12 else -1.0

    if abs(k2) < 1e-9:
        if abs(k1) < 1e-12:
            return None
        v = -k0 / k1
        return (_u_of(v), v)

    disc = k1 * k1 - 4.0 * k0 * k2
    if disc < 0.0:
        return None
    w = math.sqrt(disc)
    v1 = (-k1 - w) / (2.0 * k2)
    u1 = _u_of(v1)
    if 0.0 <= u1 <= 1.0 and 0.0 <= v1 <= 1.0:
        return (u1, v1)
    v2 = (-k1 + w) / (2.0 * k2)
    return (_u_of(v2), v2)


def bend_canvas(
    src: Canvas,
    rest: Sequence[Sequence[float]],
    pose: Sequence[Sequence[float]],
    reach: float | None = None,
    target: Canvas | None = None,
    offset_x: int = 0,
    offset_y: int = 0,
) -> Canvas:
    """Deform `src` from polyline `rest` to `pose` via inverse-bilinear strip mapping."""
    rest_pts = [(float(p[0]), float(p[1])) for p in rest]
    pose_pts = [(float(p[0]), float(p[1])) for p in pose]
    if len(rest_pts) < 2 or len(pose_pts) != len(rest_pts):
        raise ValueError("rest and pose polylines must have the same length (>= 2)")

    out = target if target is not None else Canvas(src.width, src.height, fill=TRANSPARENT)

    eff_reach = reach
    if eff_reach is None:
        eff_reach = 1.0
        for y in range(src.height):
            for x in range(src.width):
                if src.pixels[y * src.width + x][3] == 0:
                    continue
                min_d2 = float("inf")
                for i in range(len(rest_pts) - 1):
                    d2 = _seg_dist2(
                        x + 0.5, y + 0.5,
                        rest_pts[i][0], rest_pts[i][1],
                        rest_pts[i + 1][0], rest_pts[i + 1][1],
                    )
                    if d2 < min_d2:
                        min_d2 = d2
                eff_reach = max(eff_reach, math.sqrt(min_d2) + 1.5)

    r_strip = build_strip(rest_pts, eff_reach)
    q_strip = build_strip(pose_pts, eff_reach)

    all_q = [pt for pair in q_strip for pt in pair]
    x0 = math.floor(min(p[0] for p in all_q))
    x1 = math.ceil(max(p[0] for p in all_q))
    y0 = math.floor(min(p[1] for p in all_q))
    y1 = math.ceil(max(p[1] for p in all_q))
    bw = x1 - x0 + 1
    bh = y1 - y0 + 1
    if bw <= 0 or bh <= 0:
        return out
    done = bytearray(bw * bh)

    for i in range(len(q_strip) - 1):
        a, d = q_strip[i][0], q_strip[i][1]
        b, c = q_strip[i + 1][0], q_strip[i + 1][1]
        ra, rd = r_strip[i][0], r_strip[i][1]
        rb, rc = r_strip[i + 1][0], r_strip[i + 1][1]

        qx0 = math.floor(min(a[0], b[0], c[0], d[0]))
        qx1 = math.ceil(max(a[0], b[0], c[0], d[0]))
        qy0 = math.floor(min(a[1], b[1], c[1], d[1]))
        qy1 = math.ceil(max(a[1], b[1], c[1], d[1]))

        for py in range(qy0, qy1 + 1):
            for px in range(qx0, qx1 + 1):
                di = (py - y0) * bw + (px - x0)
                if done[di]:
                    continue
                uv = inv_bilinear(px + 0.5, py + 0.5, a, b, c, d)
                if uv is None:
                    continue
                u, v = uv
                if u < -1e-6 or u > 1.0 + 1e-6 or v < -1e-6 or v > 1.0 + 1e-6:
                    continue
                iu, iv = 1.0 - u, 1.0 - v
                sx = math.floor(ra[0] * iu * iv + rb[0] * u * iv + rc[0] * u * v + rd[0] * iu * v)
                sy = math.floor(ra[1] * iu * iv + rb[1] * u * iv + rc[1] * u * v + rd[1] * iu * v)
                if not src.in_bounds(sx, sy):
                    continue
                col = src.get_pixel(sx, sy)
                if col[3] == 0:
                    continue
                done[di] = 1
                out.set_pixel(px + offset_x, py + offset_y, col)
    return out


def draw_ik_limb(
    canvas: Canvas,
    start: Sequence[float],
    target: Sequence[float],
    l1: float,
    l2: float,
    color: RGBA,
    direction: int = 1,
    radius_a: float = 2.0,
    radius_b: float = 1.5,
    radius_c: float | None = None,
    ramp: list[RGBA] | None = None,
) -> Point2D:
    """Solve 2-bone IK from `start` to `target` and draw a smooth shaded limb.

    Returns the computed joint position `(jx, jy)`.
    """
    hx, hy = float(start[0]), float(start[1])
    fx, fy = float(target[0]), float(target[1])
    jx, jy = solve_ik_2bone(hx, hy, fx, fy, l1, l2, direction=direction)
    rc = radius_b if radius_c is None else float(radius_c)
    eff_ramp = ramp if ramp else [darken(color, 0.72), color, brighten(color, 1.18)]
    prims = [
        {"type": "capsule", "ax": hx, "ay": hy, "bx": jx, "by": jy, "ra": float(radius_a), "rb": float(radius_b)},
        {"type": "capsule", "ax": jx, "ay": jy, "bx": fx, "by": fy, "ra": float(radius_b), "rb": rc},
    ]
    draw_solid(canvas, prims, eff_ramp, k=0.6)
    return (jx, jy)

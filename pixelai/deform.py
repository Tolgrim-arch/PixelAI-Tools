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


def knee_ik_dir(facing: int) -> int:
    """Return the anatomically correct 2-bone IK `direction` for knees given `facing` (+1 right, -1 left)."""
    return 1 if facing >= 0 else -1


def elbow_ik_dir(facing: int) -> int:
    """Return the anatomically correct 2-bone IK `direction` for elbows (bends backward away from `facing`)."""
    return -1 if facing >= 0 else 1


def walk_foot_offset(phase: float, facing: int, stride: float, lift: float) -> Point2D:
    """Compute physically accurate `(dx, dy)` foot offset for a walk/run cycle.

    Swing phase (`0 <= p < pi`): foot lifts in an arc and advances toward `+facing`.
    Stance phase (`pi <= p < 2*pi`): foot stays planted (`dy=0`) and pushes toward `-facing`,
    eliminating moonwalking and ground-clipping artifacts.
    """
    p = phase % (2.0 * math.pi)
    f = 1.0 if facing >= 0 else -1.0
    if p < math.pi:
        u = p / math.pi
        dx = f * (-stride + 2.0 * stride * u)
        dy = -math.sin(u * math.pi) * lift
    else:
        u = (p - math.pi) / math.pi
        dx = f * (stride - 2.0 * stride * u)
        dy = 0.0
    return (dx, dy)


def draw_biped_spine_rig(
    canvas: Canvas,
    cx: float | None = None,
    ground_y: float | None = None,
    facing: str | int = "right",
    action: str = "walk",
    frame: int = 0,
    total_frames: int = 12,
    body_hue: float = 270.0,
    body_sat: float = 0.65,
    eye_color: RGBA = (255, 59, 107, 255),
    horns: bool = True,
    tail: bool = True,
    scale: float = 1.0,
    shadow: bool = True,
) -> dict[str, Point2D]:
    """Render a full-body Spine + 2-bone IK animated biped creature with guaranteed anatomy and Z-order.

    Guarantees:
    - Forward-consistent gait (swing advances toward `facing`, stance pushes `-facing`).
    - Both knees bend toward `facing`; both elbows bend away from `facing`.
    - Strict back-to-front Z-order: shadow -> far arm -> far leg -> tail -> spine body -> near leg -> near arm.
    - Far limbs are depth-darkened for clean silhouette separation.
    - Hip, shoulder, and tail anchors derive directly from the posed spine nodes.
    """
    from pixelai.color import hue_ramp

    f_dir = -1 if str(facing).strip().lower() in ("left", "-1", "l") else 1
    act = str(action).strip().lower()
    t = (frame % max(1, total_frames)) / max(1, total_frames)
    phase = t * 2.0 * math.pi

    sc = max(0.4, float(scale))
    center_x = float(cx) if cx is not None else canvas.width * 0.5
    gy = float(ground_y) if ground_y is not None else canvas.height - max(4.0, 7.0 * sc)

    # Action gait parameters
    if act == "run":
        stride = 8.5 * sc
        lift = 6.5 * sc
        arm_amp = 7.5 * sc
        bob_amp = 3.2 * sc
        lean_base = 2.8 * sc * f_dir
    elif act == "idle":
        stride = 0.0
        lift = 0.0
        arm_amp = 1.4 * sc
        bob_amp = 1.2 * sc
        lean_base = 0.6 * sc * f_dir
    elif act == "attack":
        stride = 2.0 * sc
        lift = 1.5 * sc
        arm_amp = 10.0 * sc
        bob_amp = 1.8 * sc
        lean_base = (3.5 * sc if 0.25 <= t <= 0.65 else -1.5 * sc) * f_dir
    else:  # walk
        stride = 6.5 * sc
        lift = 4.8 * sc
        arm_amp = 5.5 * sc
        bob_amp = 2.2 * sc
        lean_base = 1.6 * sc * f_dir

    # Color ramps (near limbs full brightness, far limbs depth-darkened ~20%)
    body_ramp = hue_ramp(5, hue=body_hue, shift=45.0, sat=body_sat, light=(0.16, 0.75))
    near_limb_ramp = hue_ramp(4, hue=body_hue - 4.0, shift=40.0, sat=body_sat * 0.92, light=(0.18, 0.72))
    far_limb_ramp = hue_ramp(4, hue=body_hue - 8.0, shift=35.0, sat=body_sat * 0.80, light=(0.11, 0.54))
    tail_ramp = hue_ramp(5, hue=body_hue + 10.0, shift=45.0, sat=body_sat, light=(0.15, 0.70))

    # Build neutral torso + head + horns + 3/4 face on local canvas
    w, h = canvas.width, canvas.height
    body_def = Canvas(w, h)
    hip_y = gy - 15.0 * sc
    chest_y = hip_y - 10.0 * sc
    neck_y = chest_y - 8.0 * sc
    head_y = neck_y - 5.0 * sc

    prims: list[dict] = [
        {"type": "capsule", "ax": center_x, "ay": neck_y + 2.0 * sc, "bx": center_x, "by": hip_y, "ra": 6.8 * sc, "rb": 8.2 * sc},
        {"type": "ellipse", "x": center_x + 1.0 * sc * f_dir, "y": head_y + 2.0 * sc, "rx": 7.0 * sc, "ry": 6.0 * sc},
    ]
    if horns:
        prims.append({
            "type": "capsule",
            "ax": center_x - 3.5 * sc * f_dir, "ay": head_y - 2.0 * sc,
            "bx": center_x - 6.5 * sc * f_dir, "by": head_y - 9.0 * sc,
            "ra": 2.2 * sc, "rb": 0.8 * sc,
        })
        prims.append({
            "type": "capsule",
            "ax": center_x + 3.5 * sc * f_dir, "ay": head_y - 2.0 * sc,
            "bx": center_x + 6.5 * sc * f_dir, "by": head_y - 8.5 * sc,
            "ra": 2.0 * sc, "rb": 0.8 * sc,
        })

    draw_solid(
        body_def,
        primitives=prims,
        ramp=body_ramp,
        light=(-0.55 * f_dir, -0.65, 0.52),
        k=0.9,
        inflate=2.2 * sc,
        gloss=0.22,
        dither_strip=0.25,
    )

    # 3/4 profile face oriented toward `facing`
    eye_y = int(round(head_y + 0.5 * sc))
    eye_far_x = int(round(center_x + 0.5 * sc * f_dir))
    eye_near_x = int(round(center_x + 4.5 * sc * f_dir))
    ew = max(1, int(round(2 * sc)))
    eh = max(2, int(round(2.5 * sc)))
    for ex in (eye_far_x, eye_near_x):
        body_def.draw_rect(ex - ew // 2, eye_y, ew, eh, eye_color)
        body_def.set_pixel(ex - ew // 2 + (1 if f_dir > 0 else 0), eye_y + 1, (255, 245, 180, 255))
    mouth_x = int(round(center_x + 2.5 * sc * f_dir))
    mouth_y = int(round(head_y + 5.0 * sc))
    mw = max(3, int(round(6 * sc)))
    body_def.draw_rect(mouth_x - mw // 2, mouth_y, mw, max(1, int(round(2 * sc))), (24, 14, 34, 255))
    body_def.set_pixel(mouth_x - mw // 2 + 1, mouth_y, (245, 236, 215, 255))
    body_def.set_pixel(mouth_x + mw // 2 - 1, mouth_y, (245, 236, 215, 255))

    # Spine rest & posed nodes (hip -> chest -> neck -> head)
    # Double-frequency vertical bounce: lowest on contact, highest on passing
    bob = -abs(math.sin(phase)) * bob_amp if act != "idle" else math.sin(phase) * bob_amp
    sway = math.sin(phase) * (1.2 * sc) if act != "idle" else 0.0
    rest_body = [
        (center_x, hip_y),
        (center_x, chest_y),
        (center_x, neck_y),
        (center_x, head_y),
    ]
    pose_body = [
        (center_x + sway * 0.4, hip_y + bob),
        (center_x + sway * 0.6 + lean_base * 0.45, chest_y + bob),
        (center_x + sway * 0.8 + lean_base * 0.85, neck_y + bob * 1.05),
        (center_x + sway * 1.0 + lean_base * 1.15, head_y + bob * 1.1),
    ]

    hip_node = pose_body[0]
    chest_node = pose_body[1]
    l1_leg, l2_leg = 8.5 * sc, 8.5 * sc
    l1_arm, l2_arm = 7.0 * sc, 7.0 * sc
    k_dir = knee_ik_dir(f_dir)
    e_dir = elbow_ik_dir(f_dir)

    # Compute foot targets (near leg = phase, far leg = phase + pi)
    near_foot_dx, near_foot_dy = walk_foot_offset(phase, f_dir, stride, lift)
    far_foot_dx, far_foot_dy = walk_foot_offset(phase + math.pi, f_dir, stride, lift)
    if act == "idle":
        near_foot_dx, far_foot_dx = -2.0 * sc * f_dir, 2.5 * sc * f_dir

    near_hip = (hip_node[0] - 1.5 * sc * f_dir, hip_node[1])
    far_hip = (hip_node[0] + 2.2 * sc * f_dir, hip_node[1] - 0.5 * sc)
    near_foot = (center_x - 1.0 * sc * f_dir + near_foot_dx, gy + near_foot_dy)
    far_foot = (center_x + 2.0 * sc * f_dir + far_foot_dx, gy - 0.5 * sc + far_foot_dy)

    # Compute hand targets (counter-swing opposite to legs)
    arm_wave = math.cos(phase)
    near_shoulder = (chest_node[0] - 2.0 * sc * f_dir, chest_node[1] + 1.0 * sc)
    far_shoulder = (chest_node[0] + 4.0 * sc * f_dir, chest_node[1] + 0.5 * sc)
    if act == "attack":
        punch = math.sin(phase) * arm_amp * f_dir
        near_hand = (near_shoulder[0] + 5.0 * sc * f_dir + punch, near_shoulder[1] + 4.0 * sc - abs(punch) * 0.35)
        far_hand = (far_shoulder[0] + 3.0 * sc * f_dir - punch * 0.4, far_shoulder[1] + 6.0 * sc)
    else:
        near_hand = (near_shoulder[0] + (-arm_wave * arm_amp) * f_dir, near_shoulder[1] + 10.0 * sc - abs(arm_wave) * 1.8 * sc)
        far_hand = (far_shoulder[0] + (arm_wave * arm_amp) * f_dir, far_shoulder[1] + 9.5 * sc - abs(arm_wave) * 1.5 * sc)

    # 1. Ground shadow (opaque dark ellipse marked as shadow so GIF preserves it)
    if shadow:
        canvas.mark_shadow = True
        canvas.mark_no_outline = True
        sh_rx = max(4, int(round((12.0 - bob * 0.35) * sc)))
        canvas.draw_ellipse(int(round(center_x)), int(round(gy + 1.0)), sh_rx, max(2, int(round(2.5 * sc))), (22, 16, 30, 180), filled=True)
        canvas.mark_shadow = False
        canvas.mark_no_outline = False

    # 2. Far arm (behind body, depth-darkened)
    draw_ik_limb(
        canvas, far_shoulder, far_hand, l1_arm, l2_arm, far_limb_ramp[2],
        direction=e_dir, radius_a=2.1 * sc, radius_b=1.6 * sc, radius_c=1.4 * sc, ramp=far_limb_ramp,
    )

    # 3. Far leg (behind body, depth-darkened)
    far_knee = draw_ik_limb(
        canvas, far_hip, far_foot, l1_leg, l2_leg, far_limb_ramp[2],
        direction=k_dir, radius_a=2.6 * sc, radius_b=2.0 * sc, radius_c=1.8 * sc, ramp=far_limb_ramp,
    )

    # 4. Spine tail extending toward -facing, anchored strictly at hip_node
    if tail:
        tail_def = Canvas(w, h)
        tx0 = center_x - 3.0 * sc * f_dir
        tx1 = tx0 - 20.0 * sc * f_dir
        ty0 = hip_y - 1.0 * sc
        draw_solid(
            tail_def,
            primitives=[
                {"type": "capsule", "ax": tx0, "ay": ty0, "bx": tx1, "by": ty0, "ra": 4.2 * sc, "rb": 1.4 * sc},
                {"type": "ellipse", "x": tx0 - 7.0 * sc * f_dir, "y": ty0 - 4.0 * sc, "rx": 1.6 * sc, "ry": 2.4 * sc},
                {"type": "ellipse", "x": tx0 - 13.0 * sc * f_dir, "y": ty0 - 3.5 * sc, "rx": 1.4 * sc, "ry": 2.0 * sc},
                {"type": "ellipse", "x": tx0 - 18.0 * sc * f_dir, "y": ty0 - 2.5 * sc, "rx": 1.1 * sc, "ry": 1.5 * sc},
            ],
            ramp=tail_ramp,
            light=(-0.55 * f_dir, -0.65, 0.52),
            k=0.7,
            dither_strip=0.25,
        )
        rest_tail = [
            (tx0, ty0),
            (tx0 - 7.0 * sc * f_dir, ty0),
            (tx0 - 14.0 * sc * f_dir, ty0),
            (tx1, ty0),
        ]
        pose_tail = wave_polyline(rest_tail, t=t, amp=4.0 * sc, wavelength=20.0 * sc, anchor_from=0.1)
        dx_hip = hip_node[0] - center_x
        dy_hip = hip_node[1] - hip_y
        pose_tail = [(px + dx_hip, py + dy_hip) for px, py in pose_tail]
        bend_canvas(tail_def, rest=rest_tail, pose=pose_tail, target=canvas)

    # 5. Full-body Spine torso + head + horns
    bend_canvas(body_def, rest=rest_body, pose=pose_body, target=canvas)

    # 6. Near leg (in front of body, full brightness)
    near_knee = draw_ik_limb(
        canvas, near_hip, near_foot, l1_leg, l2_leg, near_limb_ramp[2],
        direction=k_dir, radius_a=2.7 * sc, radius_b=2.1 * sc, radius_c=1.9 * sc, ramp=near_limb_ramp,
    )

    # 7. Near arm (in front of body, full brightness — never occluded by torso)
    near_elbow = draw_ik_limb(
        canvas, near_shoulder, near_hand, l1_arm, l2_arm, near_limb_ramp[2],
        direction=e_dir, radius_a=2.2 * sc, radius_b=1.7 * sc, radius_c=1.5 * sc, ramp=near_limb_ramp,
    )

    return {
        "hip": hip_node,
        "chest": chest_node,
        "near_knee": near_knee,
        "far_knee": far_knee,
        "near_foot": near_foot,
        "far_foot": far_foot,
        "near_elbow": near_elbow,
        "near_hand": near_hand,
    }


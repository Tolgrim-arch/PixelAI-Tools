"""Organic SDF metaball solids and FBM-driven procedural flame/smoke effects."""

from __future__ import annotations

import math
from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import RGBA, bayer_threshold, dither_band_index, lerp_rgba

FLAME_RAMP: tuple[RGBA, ...] = (
    (110, 22, 8, 255),
    (185, 45, 10, 255),
    (232, 96, 20, 255),
    (250, 156, 40, 255),
    (255, 212, 96, 255),
    (255, 246, 206, 255),
)

SMOKE_RAMP: tuple[RGBA, ...] = (
    (140, 140, 148, 255),
    (155, 155, 163, 255),
    (170, 170, 178, 255),
    (185, 185, 193, 255),
    (200, 200, 207, 255),
    (214, 214, 220, 255),
)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else (hi if v > hi else v)


def _hash2d(a: int, b: int, seed: int = 0) -> float:
    h = (a * 374761393 + b * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = (h ^ (h >> 16)) & 0xFFFFFFFF
    return h / 4294967296.0


def value_noise(x: float, y: float, seed: int = 0) -> float:
    """Deterministic smooth 2D value noise in [0, 1]."""
    ix = math.floor(x)
    iy = math.floor(y)
    fx = x - ix
    fy = y - iy
    sx = fx * fx * (3.0 - 2.0 * fx)
    sy = fy * fy * (3.0 - 2.0 * fy)
    a = _hash2d(ix, iy, seed)
    b = _hash2d(ix + 1, iy, seed)
    c = _hash2d(ix, iy + 1, seed)
    d = _hash2d(ix + 1, iy + 1, seed)
    return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy


def fbm(x: float, y: float, octaves: int = 4, seed: int = 0) -> float:
    """Fractal Brownian motion built from deterministic 2D value noise."""
    total = 0.0
    amp = 0.5
    freq = 1.0
    norm = 0.0
    for i in range(max(1, octaves)):
        total += value_noise(x * freq, y * freq, seed + i * 17) * amp
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm if norm > 0.0 else 0.0


def shape_height(prim: dict[str, Any], x: float, y: float) -> float:
    """Evaluate dome height for an organic capsule or rotated ellipsoid primitive."""
    kind = str(prim.get("type", "")).lower()
    is_ell = kind in ("ellipse", "ell", "ellipsoid") or ("rx" in prim and "ry" in prim)
    if is_ell:
        rot = float(prim.get("rot", 0.0))
        c, s = math.cos(rot), math.sin(rot)
        px = float(prim.get("x", prim.get("cx", 0.0)))
        py = float(prim.get("y", prim.get("cy", 0.0)))
        rx = max(1e-4, float(prim["rx"]))
        ry = max(1e-4, float(prim["ry"]))
        dx, dy = x - px, y - py
        u = (dx * c + dy * s) / rx
        v = (-dx * s + dy * c) / ry
        q = u * u + v * v
        return math.sqrt(1.0 - q) * min(rx, ry) if q < 1.0 else 0.0

    ax = float(prim["ax"])
    ay = float(prim["ay"])
    bx = float(prim["bx"])
    by = float(prim["by"])
    ra = float(prim.get("ra", prim.get("r", 2.0)))
    rb = float(prim.get("rb", ra))
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    u = _clamp(((x - ax) * dx + (y - ay) * dy) / l2) if l2 > 1e-9 else 0.0
    r = ra + (rb - ra) * u
    d = math.hypot(x - ax - dx * u, y - ay - dy * u)
    return math.sqrt(r * r - d * d) if d < r else 0.0


def draw_solid(
    canvas: Canvas,
    primitives: list[dict[str, Any]],
    ramp: list[RGBA],
    light: tuple[float, float, float] = (-0.55, -0.65, 0.52),
    k: float = 0.8,
    ambient: float = 0.24,
    dark: float = 1.0,
    gloss: float = 0.0,
    shine: float = 10.0,
    cut: float = 0.12,
    inflate: float = 0.0,
    inflate_mix: float = 0.75,
    dither_strip: float = 0.0,
) -> None:
    """Render a smooth-min metaball union of capsules/ellipsoids with normal-mapped shading."""
    if not primitives or not ramp:
        return

    ll = math.hypot(light[0], light[1], light[2]) or 1.0
    lx, ly, lz = light[0] / ll, light[1] / ll, light[2] / ll
    hl = math.hypot(lx, ly, lz + 1.0) or 1.0
    hx, hy, hz = lx / hl, ly / hl, (lz + 1.0) / hl
    smooth_k = max(0.05, float(k))

    x0, x1 = float("inf"), float("-inf")
    y0, y1 = float("inf"), float("-inf")
    for p in primitives:
        is_ell = str(p.get("type", "")).lower() in ("ellipse", "ell", "ellipsoid") or ("rx" in p and "ry" in p)
        if is_ell:
            r = max(float(p["rx"]), float(p["ry"]))
            px = float(p.get("x", p.get("cx", 0.0)))
            py = float(p.get("y", p.get("cy", 0.0)))
            x0, x1 = min(x0, px - r), max(x1, px + r)
            y0, y1 = min(y0, py - r), max(y1, py + r)
        else:
            r = max(float(p.get("ra", p.get("r", 2.0))), float(p.get("rb", p.get("ra", p.get("r", 2.0)))))
            ax, ay = float(p["ax"]), float(p["ay"])
            bx, by = float(p["bx"]), float(p["by"])
            x0, x1 = min(x0, min(ax, bx) - r), max(x1, max(ax, bx) + r)
            y0, y1 = min(y0, min(ay, by) - r), max(y1, max(ay, by) + r)

    def _hf(px: float, py: float) -> float:
        s = 0.0
        any_hit = False
        for p in primitives:
            h = shape_height(p, px, py)
            if h > 0.0:
                s += math.exp(min(60.0, h / smooth_k))
                any_hit = True
        return smooth_k * math.log(s) if any_hit else 0.0

    gx0 = math.floor(x0) - 1
    gy0 = math.floor(y0) - 1
    gw = math.ceil(x1) - gx0 + 2
    gh = math.ceil(y1) - gy0 + 2
    grid: list[float] | None = None

    if inflate > 0.0 and gw > 2 and gh > 2:
        hp = [0.0] * (gw * gh)
        dist = [0.0] * (gw * gh)
        for j in range(gh):
            for i in range(gw):
                h = _hf(gx0 + i, gy0 + j)
                hp[j * gw + i] = h
                dist[j * gw + i] = 1e6 if h > cut else 0.0
        for j in range(gh):
            for i in range(gw):
                idx = j * gw + i
                if dist[idx] == 0.0:
                    continue
                if i > 0:
                    dist[idx] = min(dist[idx], dist[idx - 1] + 1.0)
                if j > 0:
                    d_up = dist[idx - gw] + 1.0
                    d_ul = dist[idx - gw - 1] + 1.414 if i > 0 else 1e6
                    d_ur = dist[idx - gw + 1] + 1.414 if i < gw - 1 else 1e6
                    dist[idx] = min(dist[idx], d_up, d_ul, d_ur)
        for j in range(gh - 1, -1, -1):
            for i in range(gw - 1, -1, -1):
                idx = j * gw + i
                if dist[idx] == 0.0:
                    continue
                if i < gw - 1:
                    dist[idx] = min(dist[idx], dist[idx + 1] + 1.0)
                if j < gh - 1:
                    d_dn = dist[idx + gw] + 1.0
                    d_dr = dist[idx + gw + 1] + 1.414 if i < gw - 1 else 1e6
                    d_dl = dist[idx + gw - 1] + 1.414 if i > 0 else 1e6
                    dist[idx] = min(dist[idx], d_dn, d_dr, d_dl)
        rad = float(inflate)
        mix = _clamp(float(inflate_mix))
        grid = [0.0] * (gw * gh)
        for idx in range(gw * gh):
            if dist[idx] > 0.0:
                t = min(dist[idx], rad)
                dome = math.sqrt(max(0.0, rad * rad - (rad - t) * (rad - t)))
                grid[idx] = dome * mix + hp[idx] * (1.0 - mix)

    def _sample_grid(px: int, py: int) -> float:
        assert grid is not None
        ix = max(0, min(gw - 1, px - gx0))
        iy = max(0, min(gh - 1, py - gy0))
        return grid[iy * gw + ix]

    y_start = max(0, math.floor(y0))
    y_end = min(canvas.height - 1, math.ceil(y1))
    x_start = max(0, math.floor(x0))
    x_end = min(canvas.width - 1, math.ceil(x1))
    n = len(ramp)

    for y in range(y_start, y_end + 1):
        for x in range(x_start, x_end + 1):
            if grid is not None:
                h = _sample_grid(x, y)
                if h <= 0.0:
                    continue
                nx = -(_sample_grid(x + 1, y) - _sample_grid(x - 1, y)) * 0.5
                ny = -(_sample_grid(x, y + 1) - _sample_grid(x, y - 1)) * 0.5
            else:
                h = _hf(x, y)
                if h <= cut:
                    continue
                nx = -(_hf(x + 0.5, y) - _hf(x - 0.5, y))
                ny = -(_hf(x, y + 0.5) - _hf(x, y - 0.5))

            nl = math.hypot(nx, ny, 1.0)
            diff = max(0.0, (nx * lx + ny * ly + lz) / nl)
            spec = (max(0.0, (nx * hx + ny * hy + hz) / nl) ** shine) * gloss if gloss > 0.0 else 0.0
            v = (ambient + (1.0 - ambient) * diff + spec) * dark
            idx = dither_band_index(_clamp(v), n, x, y, strip=dither_strip)
            canvas.set_pixel(x, y, ramp[idx])


def _draw_flow(
    canvas: Canvas,
    x: float,
    ground: float,
    t: float,
    ramp: list[RGBA],
    height: float,
    width: float,
    speed: float,
    fx: float,
    fy: float,
    rough: float,
    sway: float,
    sway_amp: float,
    warp: float,
    calm: float,
    cut: float,
    gain: float,
    dither_strip: float,
    profile_fn,
    value_fn,
    alphas: list[float] | None = None,
    seed: int = 9,
    embers: int = 0,
) -> None:
    if not ramp or height <= 0.0 or width <= 0.0:
        return
    n = len(ramp)
    top = ground - height * 1.35
    bot = ground + height * 0.12
    wide = max(profile_fn(-0.12 + (k / 16.0) * 1.47) for k in range(17))
    reach = width * wide * 1.6 + sway_amp + warp
    x0 = max(0, math.floor(x - reach))
    x1 = min(canvas.width - 1, math.ceil(x + reach))
    y0 = max(0, math.floor(top))
    y1 = min(canvas.height - 1, math.ceil(bot))

    for wy in range(y0, y1 + 1):
        h = (ground - wy) / height
        pw = profile_fn(h)
        if pw <= 0.0:
            continue
        sway_off = (fbm(h * 1.5, t * sway, 2, 7 + seed) - 0.5) * sway_amp * h * h
        hw = max(0.5, width * pw)
        for wx in range(x0, x1 + 1):
            sx = wx - sway_off
            if warp > 0.0:
                sx += (fbm(sx * fx * 0.6, wy * fy * 0.6 + t * speed * 0.6, 2, 3 + seed) - 0.5) * warp * max(0.0, h)
            dx = (sx - x) / hw
            nz = fbm(sx * fx, wy * fy + t * speed, 3, 1 + seed)
            v = value_fn(dx, h) + (nz - 0.5) * rough * (calm + h)
            if v <= cut:
                continue
            k = dither_band_index(_clamp(v * gain), n, wx, wy, strip=dither_strip)
            col = ramp[k]
            if not alphas:
                canvas.set_pixel(wx, wy, col)
            else:
                a_f = alphas[min(len(alphas) - 1, k)]
                dst = canvas.get_pixel(wx, wy)
                if dst[3] > 0:
                    blended = lerp_rgba(dst, (col[0], col[1], col[2], dst[3]), a_f)
                    canvas.set_pixel(wx, wy, blended)
                else:
                    canvas.set_pixel(wx, wy, (col[0], col[1], col[2], max(1, min(255, int(round(a_f * 255.0))))))

    # Deterministic rising embers/sparks
    if embers > 0 and n >= 2:
        for i in range(embers):
            phase = (_hash2d(i, 1, seed) + t * 0.85) % 1.0
            ex = int(round(x + (_hash2d(i, 2, seed) - 0.5) * width * 1.4 + math.sin(phase * math.pi * 4.0 + i) * 1.5))
            ey = int(round(ground - height * (0.45 + phase * 0.85)))
            if bayer_threshold(ex, ey) < (1.0 - phase):
                ec = ramp[n - 1 if phase < 0.45 else max(0, n - 2)]
                canvas.set_pixel(ex, ey, ec)


def draw_flame(
    canvas: Canvas,
    x: float,
    ground: float,
    t: float = 0.0,
    height: float = 28.0,
    width: float = 9.0,
    ramp: list[RGBA] | None = None,
    speed: float = 3.4,
    rough: float = 1.45,
    sway_amp: float = 5.0,
    dither_strip: float = 0.4,
    seed: int = 9,
    embers: int = 4,
) -> None:
    """Draw a deterministic FBM-driven pixel-art flame at `(x, ground)` for time `t`."""
    cols = ramp if ramp else list(FLAME_RAMP)
    _draw_flow(
        canvas=canvas,
        x=x,
        ground=ground,
        t=t,
        ramp=cols,
        height=height,
        width=width,
        speed=speed,
        fx=0.16,
        fy=0.11,
        rough=rough,
        sway=1.6,
        sway_amp=sway_amp,
        warp=0.0,
        calm=0.35,
        cut=0.04,
        gain=1.02,
        dither_strip=dither_strip,
        profile_fn=lambda h: (max(0.0, 1.0 - h * 0.85) ** 0.9) * math.sqrt(_clamp((h + 0.08) / 0.18)),
        value_fn=lambda dx, h: 1.0 - h * 1.05 - dx * dx * 0.75,
        alphas=None,
        seed=seed,
        embers=embers,
    )


def draw_smoke(
    canvas: Canvas,
    x: float,
    ground: float,
    t: float = 0.0,
    height: float = 40.0,
    width: float = 2.5,
    ramp: list[RGBA] | None = None,
    speed: float = 1.5,
    rough: float = 1.3,
    sway_amp: float = 5.0,
    warp: float = 22.0,
    dither_strip: float = 0.5,
    seed: int = 13,
) -> None:
    """Draw a deterministic FBM-warped translucent pixel-art smoke plume at `(x, ground)`."""
    cols = ramp if ramp else list(SMOKE_RAMP)
    alphas = [0.12 + 0.73 * (i / max(1, len(cols) - 1)) for i in range(len(cols))]
    _draw_flow(
        canvas=canvas,
        x=x,
        ground=ground,
        t=t,
        ramp=cols,
        height=height,
        width=width,
        speed=speed,
        fx=0.12,
        fy=0.09,
        rough=rough,
        sway=0.7,
        sway_amp=sway_amp,
        warp=warp,
        calm=0.03,
        cut=0.02,
        gain=1.1,
        dither_strip=dither_strip,
        profile_fn=lambda h: 0.0 if h < -0.02 else 0.8 + h * 4.5,
        value_fn=lambda dx, h: 0.8 - h * 0.5 - dx * dx * 0.65 - max(0.0, h - 0.4) * 0.9,
        alphas=alphas,
        seed=seed,
        embers=0,
    )

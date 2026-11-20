"""Reusable, composable post-processing animation FX for finished pixel art canvases."""

from __future__ import annotations

import math
from random import Random
from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import (
    RGBA,
    TRANSPARENT,
    blend_add,
    blend_screen,
    lerp_rgba,
    luminance,
    parse_color,
)

FX_DEFAULTS: dict[str, int] = {
    "sheen_sweep": 12,
    "sparkle_glint": 8,
    "bounce": 8,
    "float_bob": 8,
    "aura_glow": 8,
    "hit_flash": 6,
    "wind_sway": 8,
}


def _sprite_bounds(canvas: Canvas) -> tuple[int, int, int, int] | None:
    """Return (min_x, min_y, max_x, max_y) of non-shadow opaque pixels."""
    min_x, min_y = canvas.width, canvas.height
    max_x, max_y = -1, -1
    for y in range(canvas.height):
        for x in range(canvas.width):
            idx = y * canvas.width + x
            if canvas.pixels[idx][3] > 0 and idx not in canvas.shadow_pixels:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x < min_x:
        return None
    return (min_x, min_y, max_x, max_y)


def _is_outline_pixel(canvas: Canvas, x: int, y: int) -> bool:
    idx = y * canvas.width + x
    px = canvas.pixels[idx]
    if px[3] == 0 or idx in canvas.shadow_pixels or idx in canvas.no_outline:
        return False
    if luminance(px) >= 75:
        return False
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if not canvas.in_bounds(nx, ny):
            return True
        nidx = ny * canvas.width + nx
        if canvas.pixels[nidx][3] == 0 or nidx in canvas.shadow_pixels:
            return True
    return False


def apply_sheen_sweep(
    canvas: Canvas,
    frame_idx: int,
    total_frames: int,
    color: RGBA = (255, 246, 184, 255),
    width: float = 3.0,
    angle: float = 45.0,
    blend: str = "add",
    intensity: float = 0.72,
    pause_frames: int = 4,
    include_outline: bool = False,
) -> Canvas:
    """Sweep a diagonal specular light bar across opaque sprite pixels."""
    bounds = _sprite_bounds(canvas)
    if bounds is None:
        return canvas.copy()

    active_frames = max(1, total_frames - max(0, pause_frames))
    if frame_idx >= active_frames:
        return canvas.copy()

    min_x, min_y, max_x, max_y = bounds
    rad = math.radians(angle)
    nx, ny = math.cos(rad), math.sin(rad)

    corners = (
        (min_x, min_y),
        (max_x, min_y),
        (min_x, max_y),
        (max_x, max_y),
    )
    projs = [cx * nx + cy * ny for cx, cy in corners]
    p_min, p_max = min(projs) - width, max(projs) + width
    progress = frame_idx / max(1, active_frames - 1) if active_frames > 1 else 0.5
    center = p_min + (p_max - p_min) * progress
    half_w = max(0.75, width * 0.5)

    out = canvas.copy()
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            idx = y * canvas.width + x
            px = canvas.pixels[idx]
            if px[3] == 0 or idx in canvas.shadow_pixels:
                continue
            if not include_outline and _is_outline_pixel(canvas, x, y):
                continue
            dist = abs((x * nx + y * ny) - center)
            if dist > half_w:
                continue
            falloff = 1.0 - (dist / half_w)
            amt = intensity * (0.45 + 0.55 * falloff)
            if blend == "screen":
                out.pixels[idx] = blend_screen(px, color, amt)
            elif blend == "tint":
                out.pixels[idx] = lerp_rgba(px, (*color[:3], px[3]), amt)
            else:
                out.pixels[idx] = blend_add(px, color, amt)
    return out


def apply_sparkle_glint(
    canvas: Canvas,
    frame_idx: int,
    total_frames: int,
    count: int = 3,
    color: RGBA = (255, 255, 255, 255),
    seed: int = 42,
    on_surface: bool = True,
) -> Canvas:
    """Overlay deterministic 4-point pixel starburst glints onto a Canvas."""
    bounds = _sprite_bounds(canvas)
    if bounds is None or count <= 0:
        return canvas.copy()

    min_x, min_y, max_x, max_y = bounds
    candidates: list[tuple[int, int]] = []
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            idx = y * canvas.width + x
            px = canvas.pixels[idx]
            is_opaque = px[3] > 0 and idx not in canvas.shadow_pixels
            if on_surface and is_opaque and not _is_outline_pixel(canvas, x, y):
                candidates.append((x, y))
            elif not on_surface and not is_opaque:
                # Near-silhouette empty space
                if any(
                    canvas.in_bounds(x + dx, y + dy)
                    and canvas.pixels[(y + dy) * canvas.width + (x + dx)][3] > 0
                    for dx in range(-2, 3)
                    for dy in range(-2, 3)
                ):
                    candidates.append((x, y))

    if not candidates:
        return canvas.copy()

    rng = Random(seed)
    # Bias toward upper-left / bright pixels when on surface
    if on_surface:
        candidates.sort(key=lambda pt: luminance(canvas.pixels[pt[1] * canvas.width + pt[0]]), reverse=True)
        pool = candidates[: max(count * 4, len(candidates) // 3)]
    else:
        pool = candidates
    anchors = [rng.choice(pool) for _ in range(count)]
    phases = [rng.randint(0, max(1, total_frames - 1)) for _ in range(count)]

    out = canvas.copy()
    out.mark_no_outline = True
    mid_col = lerp_rgba(color, (255, 240, 170, 255), 0.35)

    for (ax, ay), phase in zip(anchors, phases):
        local_f = (frame_idx + phase) % max(1, total_frames)
        # 4-step sparkle cycle inside the loop: 0=1px, 1=cross, 2=big_cross, 3=1px, rest=off
        if local_f == 0 or local_f == 3:
            out.set_pixel(ax, ay, color)
        elif local_f == 1:
            out.set_pixel(ax, ay, color)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                out.set_pixel(ax + dx, ay + dy, mid_col)
        elif local_f == 2:
            out.set_pixel(ax, ay, color)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                out.set_pixel(ax + dx, ay + dy, color)
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                out.set_pixel(ax + dx, ay + dy, mid_col)
    return out


def _shift_non_shadow(canvas: Canvas, dx: int = 0, dy: int = 0, squash_y: int = 0) -> Canvas:
    """Shift non-shadow pixels vertically/horizontally while keeping ground shadows anchored."""
    out = Canvas(canvas.width, canvas.height, fill=TRANSPARENT)
    out.clipped_pixels = canvas.clipped_pixels
    out.warnings = canvas.warnings.copy()

    # Keep ground shadows in place
    for idx in canvas.shadow_pixels:
        x, y = idx % canvas.width, idx // canvas.width
        out.shadow_pixels.add(idx)
        out.no_outline.add(idx)
        out.pixels[idx] = canvas.pixels[idx]

    bounds = _sprite_bounds(canvas)
    bottom_y = bounds[3] if bounds else canvas.height - 1

    for y in range(canvas.height):
        for x in range(canvas.width):
            idx = y * canvas.width + x
            if idx in canvas.shadow_pixels:
                continue
            px = canvas.pixels[idx]
            if px[3] == 0:
                continue
            ny = y + dy
            if squash_y > 0 and y < bottom_y:
                # Compress upper half down by 1px toward bottom_y
                if y <= (bounds[1] + bottom_y) // 2 if bounds else False:
                    ny += 1
            elif squash_y < 0 and y < bottom_y:
                if y <= (bounds[1] + bottom_y) // 2 if bounds else False:
                    ny -= 1
            nx = x + dx
            if out.in_bounds(nx, ny):
                nidx = ny * out.width + nx
                out.pixels[nidx] = px
                if idx in canvas.no_outline:
                    out.no_outline.add(nidx)
    return out


def apply_bounce(
    canvas: Canvas,
    frame_idx: int,
    total_frames: int,
    height: int = 3,
    squash: bool = True,
) -> Canvas:
    """Apply a grounded jump/bounce cycle with optional 1px squash & stretch."""
    t = frame_idx / max(1, total_frames)
    # Parabolic arc for first 75% of cycle, grounded squash at end
    if t < 0.75:
        u = t / 0.75
        arc = 4.0 * u * (1.0 - u)
        dy = -int(round(arc * height))
        sq = -1 if (squash and arc > 0.85 and height >= 2) else 0
    else:
        dy = 0
        sq = 1 if squash else 0
    return _shift_non_shadow(canvas, dx=0, dy=dy, squash_y=sq)


def apply_float_bob(
    canvas: Canvas,
    frame_idx: int,
    total_frames: int,
    amplitude: int = 2,
) -> Canvas:
    """Apply smooth sinusoidal vertical levitation."""
    angle = (frame_idx / max(1, total_frames)) * 2.0 * math.pi
    dy = -int(round((math.sin(angle) * 0.5 + 0.5) * amplitude))
    return _shift_non_shadow(canvas, dx=0, dy=dy, squash_y=0)


def apply_aura_glow(
    canvas: Canvas,
    frame_idx: int,
    total_frames: int,
    color: RGBA = (255, 230, 128, 160),
    radius: int = 1,
    pulse: bool = True,
) -> Canvas:
    """Add a pulsing outer rim/aura around the opaque silhouette without altering outlines."""
    out = canvas.copy()
    out.mark_no_outline = True
    phase = 0.65 + 0.35 * math.sin((frame_idx / max(1, total_frames)) * 2.0 * math.pi) if pulse else 1.0
    r_max = max(1, radius)

    for y in range(canvas.height):
        for x in range(canvas.width):
            idx = y * canvas.width + x
            if canvas.pixels[idx][3] > 0 and idx not in canvas.shadow_pixels:
                continue
            min_d = r_max + 1
            for dy in range(-r_max, r_max + 1):
                for dx in range(-r_max, r_max + 1):
                    nx, ny = x + dx, y + dy
                    if canvas.in_bounds(nx, ny):
                        nidx = ny * canvas.width + nx
                        if canvas.pixels[nidx][3] > 0 and nidx not in canvas.shadow_pixels:
                            d = abs(dx) + abs(dy)
                            if d < min_d:
                                min_d = d
            if min_d <= r_max:
                falloff = (1.0 - (min_d - 1) / max(1, r_max)) * phase
                a = max(24, min(255, int(round(color[3] * falloff))))
                out.pixels[idx] = (color[0], color[1], color[2], a)
                out.no_outline.add(idx)
    return out


def apply_hit_flash(
    canvas: Canvas,
    frame_idx: int,
    total_frames: int,
    color: RGBA = (255, 255, 255, 255),
    intensity: float = 0.85,
    flash_frames: list[int] | None = None,
) -> Canvas:
    """Apply a crisp impact/enchantment flash on selected frames."""
    targets = set(flash_frames) if flash_frames is not None else {0, 1}
    if frame_idx not in targets:
        return canvas.copy()
    out = canvas.copy()
    for idx, px in enumerate(canvas.pixels):
        if px[3] > 0 and idx not in canvas.shadow_pixels:
            out.pixels[idx] = lerp_rgba(px, (*color[:3], px[3]), intensity)
    return out


def apply_wind_sway(
    canvas: Canvas,
    frame_idx: int,
    total_frames: int,
    amplitude: int = 1,
    anchor: str = "bottom",
) -> Canvas:
    """Apply height-graduated horizontal wind shear across non-shadow pixels."""
    bounds = _sprite_bounds(canvas)
    if bounds is None or amplitude == 0:
        return canvas.copy()
    _, min_y, _, max_y = bounds
    span = max(1, max_y - min_y)
    wave = math.sin((frame_idx / max(1, total_frames)) * 2.0 * math.pi)

    out = Canvas(canvas.width, canvas.height, fill=TRANSPARENT)
    out.clipped_pixels = canvas.clipped_pixels
    out.warnings = canvas.warnings.copy()
    for idx in canvas.shadow_pixels:
        out.shadow_pixels.add(idx)
        out.no_outline.add(idx)
        out.pixels[idx] = canvas.pixels[idx]

    for y in range(canvas.height):
        t = (max_y - y) / span if anchor == "bottom" else (y - min_y) / span
        t = max(0.0, min(1.0, t))
        dx = int(round(wave * amplitude * t))
        for x in range(canvas.width):
            idx = y * canvas.width + x
            if idx in canvas.shadow_pixels:
                continue
            px = canvas.pixels[idx]
            if px[3] == 0:
                continue
            nx = x + dx
            if out.in_bounds(nx, y):
                nidx = y * out.width + nx
                out.pixels[nidx] = px
                if idx in canvas.no_outline:
                    out.no_outline.add(nidx)
    return out


def infer_fx_frame_count(fx_list: list[dict[str, Any]]) -> int:
    """Infer a sensible default frame count from a list of FX specs."""
    best = 1
    for fx in fx_list:
        kind = str(fx.get("type", fx.get("op", ""))).lower()
        period = int(fx.get("period", FX_DEFAULTS.get(kind, 8)))
        best = max(best, period)
    return best


def apply_fx_to_frame(
    canvas: Canvas,
    fx_list: list[dict[str, Any]],
    frame_idx: int,
    total_frames: int,
    palette: dict[str, RGBA] | None = None,
) -> Canvas:
    """Apply a sequence of reusable FX dicts to a single Canvas frame."""
    cur = canvas
    for fx in fx_list:
        kind = str(fx.get("type", fx.get("op", ""))).lower()
        if kind == "sheen_sweep":
            col = parse_color(fx.get("color", "#fff6b8"), palette)
            cur = apply_sheen_sweep(
                cur,
                frame_idx,
                total_frames,
                color=col,
                width=float(fx.get("width", 3.0)),
                angle=float(fx.get("angle", 45.0)),
                blend=str(fx.get("blend", "add")),
                intensity=float(fx.get("intensity", 0.72)),
                pause_frames=int(fx.get("pause_frames", 4)),
                include_outline=bool(fx.get("include_outline", False)),
            )
        elif kind == "sparkle_glint":
            col = parse_color(fx.get("color", "#ffffff"), palette)
            cur = apply_sparkle_glint(
                cur,
                frame_idx,
                total_frames,
                count=int(fx.get("count", 3)),
                color=col,
                seed=int(fx.get("seed", 42)),
                on_surface=bool(fx.get("on_surface", True)),
            )
        elif kind == "bounce":
            cur = apply_bounce(
                cur,
                frame_idx,
                total_frames,
                height=int(fx.get("height", 3)),
                squash=bool(fx.get("squash", True)),
            )
        elif kind == "float_bob":
            cur = apply_float_bob(
                cur,
                frame_idx,
                total_frames,
                amplitude=int(fx.get("amplitude", 2)),
            )
        elif kind == "aura_glow":
            col = parse_color(fx.get("color", "#ffe680a0"), palette)
            cur = apply_aura_glow(
                cur,
                frame_idx,
                total_frames,
                color=col,
                radius=int(fx.get("radius", 1)),
                pulse=bool(fx.get("pulse", True)),
            )
        elif kind == "hit_flash":
            col = parse_color(fx.get("color", "#ffffff"), palette)
            cur = apply_hit_flash(
                cur,
                frame_idx,
                total_frames,
                color=col,
                intensity=float(fx.get("intensity", 0.85)),
                flash_frames=fx.get("frames"),
            )
        elif kind == "wind_sway":
            cur = apply_wind_sway(
                cur,
                frame_idx,
                total_frames,
                amplitude=int(fx.get("amplitude", 1)),
                anchor=str(fx.get("anchor", "bottom")),
            )
        else:
            raise ValueError(f"Unknown FX type: {kind!r}")
    return cur


def apply_fx_pipeline(
    frames: list[Canvas],
    fx_list: list[dict[str, Any]],
    palette: dict[str, RGBA] | None = None,
    total_frames: int | None = None,
) -> list[Canvas]:
    """Apply composable FX to a list of frames, expanding a single static frame if needed."""
    if not fx_list:
        return frames
    target_count = total_frames if total_frames and total_frames > 0 else (
        infer_fx_frame_count(fx_list) if len(frames) == 1 else len(frames)
    )
    out: list[Canvas] = []
    for idx in range(target_count):
        base = frames[idx % len(frames)]
        out.append(apply_fx_to_frame(base, fx_list, idx, target_count, palette=palette))
    return out

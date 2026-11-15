"""Deterministic 16-tile Wang / 4-corner bitmask autotile generator."""

import math
import random
from pixelai.canvas import Canvas
from pixelai.color import RGBA, brighten as _brighten, darken as _darken


def draw_autotile_atlas(
    canvas: Canvas,
    x: int,
    y: int,
    tile_size: int,
    inner_color: RGBA,
    outer_color: RGBA,
    lip_color: RGBA | None = None,
    seed: int = 42,
) -> None:
    """Draw a 4x4 (16-tile) 4-corner Wang autotile atlas at (x, y) with seamless rounded corners.

    Bitmask per tile index (0..15):
      bit 0 (1): Top-Left (NW) is inner
      bit 1 (2): Top-Right (NE) is inner
      bit 2 (4): Bottom-Right (SE) is inner
      bit 3 (8): Bottom-Left (SW) is inner
    """
    if tile_size < 4:
        raise ValueError(f"tile_size must be >= 4, got {tile_size}")

    lip = lip_color or _darken(outer_color, 0.72)
    outer_hl = _brighten(outer_color, 1.12)
    outer_d = _darken(outer_color, 0.88)
    inner_foam = _brighten(inner_color, 1.24)
    inner_d = _darken(inner_color, 0.86)
    half = tile_size / 2.0

    for mask in range(16):
        col = mask % 4
        row = mask // 4
        tx = x + col * tile_size
        ty = y + row * tile_size

        nw = bool(mask & 1)
        ne = bool(mask & 2)
        se = bool(mask & 4)
        sw = bool(mask & 8)

        rng = random.Random(seed + mask * 17)
        grid_inner = [[False] * tile_size for _ in range(tile_size)]

        for py in range(tile_size):
            for px in range(tile_size):
                is_left = px < half
                is_top = py < half
                q_active = (
                    (nw if is_left else ne)
                    if is_top
                    else (sw if is_left else se)
                )
                adj_h = (ne if is_left else nw) if is_top else (se if is_left else sw)
                adj_v = (sw if is_top else nw) if is_left else (se if is_top else ne)
                diag_opp = (se if is_left else sw) if is_top else (ne if is_left else nw)

                cx_q = 0.0 if is_left else (tile_size - 1.0)
                cy_q = 0.0 if is_top else (tile_size - 1.0)
                dist = math.hypot(px - cx_q, py - cy_q)
                radius = half * 0.92

                in_inner = q_active
                if q_active and (not adj_h) and (not adj_v):
                    in_inner = dist <= radius
                elif (not q_active) and adj_h and adj_v and diag_opp:
                    in_inner = dist > radius

                grid_inner[py][px] = in_inner
                canvas.set_pixel(tx + px, ty + py, inner_color if in_inner else outer_color)

        # Clean 2x2 grass/ground tuft clusters inside outer, subtle 2px ripples inside inner
        if tile_size >= 8:
            tuft_count = max(1, (tile_size * tile_size) // 72)
            for _ in range(tuft_count):
                rx = rng.randint(1, tile_size - 3)
                ry = rng.randint(1, tile_size - 3)
                if not any(grid_inner[ry + dy][rx + dx] for dy in (0, 1) for dx in (0, 1)):
                    canvas.set_pixel(tx + rx, ty + ry + 1, outer_d)
                    canvas.set_pixel(tx + rx + 1, ty + ry + 1, outer_d)
                    canvas.set_pixel(tx + rx, ty + ry, outer_hl)
                    canvas.set_pixel(tx + rx + 1, ty + ry, outer_hl)
                elif all(grid_inner[ry + dy][rx + dx] for dy in (0, 1) for dx in (0, 1)):
                    canvas.set_pixel(tx + rx, ty + ry, inner_foam)
                    canvas.set_pixel(tx + rx + 1, ty + ry, inner_foam)

        # Smooth shoreline bank: earth lip under overhanging outer bank + bright inner edge highlight
        for py in range(tile_size):
            for px in range(tile_size):
                if not grid_inner[py][px]:
                    continue
                above_outer = py > 0 and not grid_inner[py - 1][px]
                side_outer = (
                    (px > 0 and not grid_inner[py][px - 1])
                    or (px + 1 < tile_size and not grid_inner[py][px + 1])
                    or (py + 1 < tile_size and not grid_inner[py + 1][px])
                )
                if above_outer:
                    canvas.set_pixel(tx + px, ty + py, lip)
                    if py + 1 < tile_size and grid_inner[py + 1][px]:
                        canvas.set_pixel(tx + px, ty + py + 1, inner_d)
                elif side_outer:
                    canvas.set_pixel(tx + px, ty + py, inner_foam)

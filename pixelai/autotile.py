"""Deterministic 16-tile Wang / 4-corner bitmask autotile generator."""

import random
from pixelai.canvas import Canvas
from pixelai.color import RGBA


def _darken(c: RGBA, factor: float = 0.78) -> RGBA:
    return (
        max(0, int(c[0] * factor)),
        max(0, int(c[1] * factor)),
        max(0, int(c[2] * factor)),
        c[3],
    )


def _brighten(c: RGBA, factor: float = 1.12) -> RGBA:
    return (
        min(255, int(c[0] * factor + 6)),
        min(255, int(c[1] * factor + 6)),
        min(255, int(c[2] * factor + 6)),
        c[3],
    )


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
    """Draw a 4x4 (16-tile) 4-corner Wang autotile atlas at (x, y).

    Bitmask per tile index (0..15):
      bit 0 (1): Top-Left (NW) is inner
      bit 1 (2): Top-Right (NE) is inner
      bit 2 (4): Bottom-Right (SE) is inner
      bit 3 (8): Bottom-Left (SW) is inner
    """
    if tile_size < 4:
        raise ValueError(f"tile_size must be >= 4, got {tile_size}")

    lip = lip_color or _darken(outer_color, 0.72)
    outer_hl = _brighten(outer_color, 1.10)
    inner_hl = _brighten(inner_color, 1.10)
    half = tile_size // 2

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

        for py in range(tile_size):
            for px in range(tile_size):
                # Normalized distance into each quadrant
                is_left = px < half
                is_top = py < half
                q_active = (
                    (nw if is_left else ne)
                    if is_top
                    else (sw if is_left else se)
                )

                # Smooth rounded transition at quadrant boundaries
                dx_center = abs(px - (half - 0.5))
                dy_center = abs(py - (half - 0.5))
                in_inner = q_active
                if not q_active:
                    # Check if adjacent quadrant pulls inward for smooth curve
                    adj_h = ne if is_left else nw if is_top else (se if is_left else sw)
                    adj_v = sw if is_top else nw if is_left else (se if is_top else ne)
                    if adj_h and adj_v and (dx_center + dy_center) < (half * 0.75):
                        in_inner = True
                else:
                    adj_h = ne if is_left else nw if is_top else (se if is_left else sw)
                    adj_v = sw if is_top else nw if is_left else (se if is_top else ne)
                    if not adj_h and not adj_v and (dx_center + dy_center) > (half * 1.15):
                        in_inner = False

                c = inner_color if in_inner else outer_color
                if rng.random() < 0.08:
                    c = inner_hl if in_inner else outer_hl
                canvas.set_pixel(tx + px, ty + py, c)

        # Add 1px lineless depth lip where top pixel is outer and current pixel is inner
        for py in range(1, tile_size):
            for px in range(tile_size):
                cur = canvas.get_pixel(tx + px, ty + py)
                above = canvas.get_pixel(tx + px, ty + py - 1)
                if cur in (inner_color, inner_hl) and above in (outer_color, outer_hl):
                    canvas.set_pixel(tx + px, ty + py, lip)

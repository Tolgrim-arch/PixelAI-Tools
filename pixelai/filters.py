"""Post-processing filters for pixel art canvases."""

from pixelai.canvas import Canvas
from pixelai.color import RGBA


def outline(canvas: Canvas, color: RGBA) -> Canvas:
    """Add a 1px 4-connected outline around non-transparent pixels."""
    out = Canvas(canvas.width, canvas.height)
    out.pixels = canvas.pixels.copy()
    for y in range(canvas.height):
        for x in range(canvas.width):
            if canvas.get_pixel(x, y)[3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if canvas.get_pixel(x + dx, y + dy)[3] > 0:
                    out.set_pixel(x, y, color)
                    break
    return out


def scale(canvas: Canvas, factor: int) -> Canvas:
    """Scale canvas by an integer factor using nearest-neighbor."""
    if factor < 1:
        raise ValueError(f"Scale factor must be >= 1, got {factor}")
    if factor == 1:
        return canvas
    out = Canvas(canvas.width * factor, canvas.height * factor)
    for y in range(canvas.height):
        for x in range(canvas.width):
            c = canvas.get_pixel(x, y)
            if c[3] == 0:
                continue
            for sy in range(factor):
                for sx in range(factor):
                    out.set_pixel(x * factor + sx, y * factor + sy, c)
    return out


def _adjust(c: RGBA, factor: float) -> RGBA:
    r, g, b, a = c
    return (
        max(0, min(255, int(r * factor))),
        max(0, min(255, int(g * factor))),
        max(0, min(255, int(b * factor))),
        a,
    )


def shade(canvas: Canvas, amount: float = 0.25) -> Canvas:
    """Apply top-left directional edge shading to non-transparent pixels."""
    out = Canvas(canvas.width, canvas.height)
    for y in range(canvas.height):
        for x in range(canvas.width):
            c = canvas.get_pixel(x, y)
            if c[3] == 0:
                continue
            top_empty = canvas.get_pixel(x, y - 1)[3] == 0
            left_empty = canvas.get_pixel(x - 1, y)[3] == 0
            bottom_empty = canvas.get_pixel(x, y + 1)[3] == 0
            right_empty = canvas.get_pixel(x + 1, y)[3] == 0
            if top_empty or left_empty:
                c = _adjust(c, 1.0 + amount)
            elif bottom_empty or right_empty:
                c = _adjust(c, 1.0 - amount)
            out.set_pixel(x, y, c)
    return out

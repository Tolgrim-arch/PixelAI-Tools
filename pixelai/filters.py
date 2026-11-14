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

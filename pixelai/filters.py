"""Post-processing filters for pixel art canvases."""

from pixelai.canvas import Canvas
from pixelai.color import RGBA


def _copy_meta(src: Canvas, dst: Canvas) -> None:
    dst.clipped_pixels = src.clipped_pixels
    dst.warnings = src.warnings.copy()


def pad(canvas: Canvas, size: int = 1) -> Canvas:
    """Expand canvas by `size` transparent pixels on all four sides."""
    if size <= 0:
        return canvas
    out = Canvas(canvas.width + size * 2, canvas.height + size * 2)
    _copy_meta(canvas, out)
    out.blit(canvas, size, size)
    return out


def _blend_selout(neighbor: RGBA, base_ink: RGBA, amount: float) -> RGBA:
    r = int(neighbor[0] * (1.0 - amount) + base_ink[0] * amount)
    g = int(neighbor[1] * (1.0 - amount) + base_ink[1] * amount)
    b = int(neighbor[2] * (1.0 - amount) + base_ink[2] * amount)
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), 255)


def outline(
    canvas: Canvas,
    color: RGBA,
    selout: bool = False,
    selout_amount: float = 0.55,
    auto_pad: bool = False,
) -> Canvas:
    """Add a 1px 4-connected outline (flat or selective) around opaque pixels."""
    if canvas.touches_border():
        if auto_pad:
            canvas = pad(canvas, 1)
        else:
            canvas.warnings.append(
                "Opaque pixels touch canvas border before 'outline'; "
                "1px outline was clipped at the edge (use larger canvas, y>=1, or auto_pad=true)."
            )

    out = canvas.copy()
    for y in range(canvas.height):
        for x in range(canvas.width):
            if canvas.get_pixel(x, y)[3] != 0:
                continue
            neighbors = [
                canvas.get_pixel(x + dx, y + dy)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if canvas.get_pixel(x + dx, y + dy)[3] > 0
            ]
            if not neighbors:
                continue
            if selout:
                # Pick darkest neighbor for crisp yet soft selective outline
                darkest = min(neighbors, key=lambda c: c[0] + c[1] + c[2])
                out.set_pixel(x, y, _blend_selout(darkest, color, selout_amount))
            else:
                out.set_pixel(x, y, color)
    return out


def scale(canvas: Canvas, factor: int) -> Canvas:
    """Scale canvas by an integer factor using nearest-neighbor."""
    if factor < 1:
        raise ValueError(f"Scale factor must be >= 1, got {factor}")
    if factor == 1:
        return canvas
    out = Canvas(canvas.width * factor, canvas.height * factor)
    _copy_meta(canvas, out)
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
    _copy_meta(canvas, out)
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


def drop_shadow(
    canvas: Canvas, dx: int = 1, dy: int = 2, color: RGBA = (33, 24, 27, 96)
) -> Canvas:
    """Cast a silhouette drop shadow onto transparent background pixels."""
    out = Canvas(canvas.width, canvas.height)
    _copy_meta(canvas, out)
    for y in range(canvas.height):
        for x in range(canvas.width):
            if canvas.get_pixel(x, y)[3] > 0:
                out.set_pixel(x + dx, y + dy, color)
    for y in range(canvas.height):
        for x in range(canvas.width):
            c = canvas.get_pixel(x, y)
            if c[3] > 0:
                out.set_pixel(x, y, c)
    return out

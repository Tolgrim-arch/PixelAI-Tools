"""Canvas and PNG inspection utilities for terminal-based AI agents."""

from pathlib import Path
from typing import Any
from PIL import Image
from pixelai.canvas import Canvas


def analyze_canvas(canvas: Canvas) -> dict[str, Any]:
    """Compute bounding box, margins, opaque pixel count, and unique colors."""
    min_x, min_y = canvas.width, canvas.height
    max_x, max_y = -1, -1
    opaque = 0
    colors: set[tuple[int, int, int, int]] = set()

    for y in range(canvas.height):
        for x in range(canvas.width):
            c = canvas.get_pixel(x, y)
            if c[3] > 0:
                opaque += 1
                colors.add(c)
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

    if opaque == 0:
        return {
            "width": canvas.width,
            "height": canvas.height,
            "opaque_pixels": 0,
            "unique_colors": 0,
            "bbox": None,
            "margins": {"top": canvas.height, "right": canvas.width, "bottom": canvas.height, "left": canvas.width},
        }

    return {
        "width": canvas.width,
        "height": canvas.height,
        "opaque_pixels": opaque,
        "unique_colors": len(colors),
        "bbox": {"x": min_x, "y": min_y, "w": max_x - min_x + 1, "h": max_y - min_y + 1},
        "margins": {
            "top": min_y,
            "right": canvas.width - 1 - max_x,
            "bottom": canvas.height - 1 - max_y,
            "left": min_x,
        },
    }


def render_ascii(canvas: Canvas, max_width: int = 64) -> str:
    """Render a compact luminance ASCII preview of the canvas for terminal inspection."""
    step = max(1, canvas.width // max_width)
    ramp = " .:-=+*#%@"
    lines: list[str] = []
    for y in range(0, canvas.height, step):
        row_chars: list[str] = []
        for x in range(0, canvas.width, step):
            r, g, b, a = canvas.get_pixel(x, y)
            if a == 0:
                row_chars.append(".")
            else:
                lum = (r * 299 + g * 587 + b * 114) // 1000
                idx = min(len(ramp) - 1, max(1, int((1.0 - lum / 255.0) * (len(ramp) - 1))))
                row_chars.append(ramp[idx])
        lines.append("".join(row_chars))
    return "\n".join(lines)


def load_png_as_canvas(path: str | Path) -> Canvas:
    """Load an existing PNG into a Canvas for inspection."""
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    canvas = Canvas(w, h)
    getter = getattr(img, "get_flattened_data", img.getdata)
    canvas.pixels = list(getter())
    return canvas

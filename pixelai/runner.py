"""Declarative JSON spec runner for pixelai-tools."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, TRANSPARENT, parse_color
from pixelai.palettes import get_palette
from pixelai import filters


def run_spec(spec: dict[str, Any]) -> Canvas:
    """Execute a declarative pixel art specification and return the resulting Canvas."""
    width = int(spec["width"])
    height = int(spec["height"])

    raw_palette = spec.get("palette", {})
    if isinstance(raw_palette, str):
        palette: dict[str, RGBA] = get_palette(raw_palette)
    else:
        palette = {k: parse_color(v) for k, v in raw_palette.items()}

    bg = parse_color(spec["background"], palette) if "background" in spec else TRANSPARENT
    canvas = Canvas(width, height, fill=bg)

    for op in spec.get("ops", []):
        kind = op["op"]
        if kind == "pixel":
            canvas.set_pixel(op["x"], op["y"], parse_color(op["color"], palette))
        elif kind == "line":
            canvas.draw_line(op["x0"], op["y0"], op["x1"], op["y1"], parse_color(op["color"], palette))
        elif kind == "rect":
            canvas.draw_rect(
                op["x"], op["y"], op["w"], op["h"],
                parse_color(op["color"], palette),
                filled=op.get("filled", True),
            )
        elif kind == "circle":
            canvas.draw_circle(
                op["cx"], op["cy"], op["r"],
                parse_color(op["color"], palette),
                filled=op.get("filled", False),
            )
        elif kind == "fill":
            canvas.flood_fill(op["x"], op["y"], parse_color(op["color"], palette))
        elif kind == "mirror_x":
            canvas.mirror_x()
        elif kind == "mirror_y":
            canvas.mirror_y()
        elif kind == "grid":
            cmap = dict(palette)
            if "colors" in op:
                cmap.update({k: parse_color(v, palette) for k, v in op["colors"].items()})
            canvas.draw_grid(op.get("x", 0), op.get("y", 0), op["rows"], cmap)
        elif kind == "dither":
            canvas.draw_dither_rect(
                op["x"], op["y"], op["w"], op["h"],
                parse_color(op["color_a"], palette),
                parse_color(op["color_b"], palette),
            )
        else:
            raise ValueError(f"Unknown op: {kind!r}")

    for post in spec.get("post", []):
        kind = post["op"]
        if kind == "outline":
            canvas = filters.outline(canvas, parse_color(post["color"], palette))
        elif kind == "shade":
            canvas = filters.shade(canvas, float(post.get("amount", 0.25)))
        elif kind == "scale":
            canvas = filters.scale(canvas, int(post["factor"]))
        else:
            raise ValueError(f"Unknown post-processing op: {kind!r}")

    return canvas

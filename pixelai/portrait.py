"""Clean cozy RPG portrait wrapper for field farmer preset."""

from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import RGBA
from pixelai.portrait_mistria import draw_mistria_portrait


def draw_field_farmer(
    canvas: Canvas,
    x: int,
    y: int,
    palette: dict[str, RGBA],
    op: dict[str, Any] | None = None,
) -> None:
    """Render a clean three-quarter cozy field farmer portrait."""
    opts: dict[str, Any] = dict(op or {})
    opts.setdefault("preset", "farmer")
    opts.setdefault("hat", True)
    opts.setdefault("width", max(48, canvas.width - x))
    opts.setdefault("height", max(64, canvas.height - y))
    draw_mistria_portrait(canvas, x, y, palette, opts)

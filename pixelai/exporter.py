"""Exporters for pixel art canvases."""

from pathlib import Path
from PIL import Image
from pixelai.canvas import Canvas


def export_png(canvas: Canvas, path: str | Path) -> Path:
    """Export a Canvas to a lossless RGBA PNG file."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (canvas.width, canvas.height))
    img.putdata(canvas.pixels)
    img.save(out_path, format="PNG")
    return out_path

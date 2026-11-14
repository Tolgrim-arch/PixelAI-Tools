"""Canvas, PNG, and multi-frame GIF inspection & QA linting utilities for AI agents."""

from collections import deque
from pathlib import Path
from typing import Any
from PIL import Image, ImageSequence
from pixelai.canvas import Canvas


def count_connected_components(canvas: Canvas) -> int:
    """Count 8-connected opaque pixel islands on a Canvas (detects detached limbs/orphans)."""
    visited: set[tuple[int, int]] = set()
    islands = 0
    for y in range(canvas.height):
        for x in range(canvas.width):
            if canvas.get_pixel(x, y)[3] > 0 and (x, y) not in visited:
                islands += 1
                queue = deque([(x, y)])
                visited.add((x, y))
                while queue:
                    cx, cy = queue.popleft()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = cx + dx, cy + dy
                            if (
                                canvas.in_bounds(nx, ny)
                                and (nx, ny) not in visited
                                and canvas.get_pixel(nx, ny)[3] > 0
                            ):
                                visited.add((nx, ny))
                                queue.append((nx, ny))
    return islands


def analyze_canvas(canvas: Canvas) -> dict[str, Any]:
    """Compute bounding box, margins, opaque pixel count, unique colors, and island count."""
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
            "islands": 0,
            "bbox": None,
            "margins": {"top": canvas.height, "right": canvas.width, "bottom": canvas.height, "left": canvas.width},
        }

    return {
        "width": canvas.width,
        "height": canvas.height,
        "opaque_pixels": opaque,
        "unique_colors": len(colors),
        "islands": count_connected_components(canvas),
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
    """Load an existing PNG (or first frame of GIF) into a Canvas for inspection."""
    with Image.open(path) as raw_img:
        img = raw_img.convert("RGBA")
        w, h = img.size
        canvas = Canvas(w, h)
        getter = getattr(img, "get_flattened_data", img.getdata)
        canvas.pixels = list(getter())
    return canvas


def load_frames_as_canvases(path: str | Path) -> list[Canvas]:
    """Load all frames of a GIF or single frame of a PNG into a list of Canvases (unrolling GIF duration multiples)."""
    raw_frames: list[tuple[Canvas, int]] = []
    with Image.open(path) as raw_img:
        for frame in ImageSequence.Iterator(raw_img):
            dur = int(frame.info.get("duration", 0) or 0)
            img = frame.convert("RGBA")
            w, h = img.size
            canvas = Canvas(w, h)
            getter = getattr(img, "get_flattened_data", img.getdata)
            canvas.pixels = list(getter())
            raw_frames.append((canvas, dur))

    valid_durs = [d for _, d in raw_frames if d > 0]
    min_dur = min(valid_durs) if valid_durs else 0
    frames: list[Canvas] = []
    for canvas, dur in raw_frames:
        repeats = max(1, int(round(dur / min_dur))) if (min_dur > 0 and dur > 0) else 1
        for _ in range(repeats):
            frames.append(canvas.copy() if len(frames) > 0 else canvas)
    return frames


def analyze_image_file(path: str | Path) -> tuple[dict[str, Any], list[Canvas]]:
    """Analyze a single-frame PNG or multi-frame GIF across all frames with QA warnings."""
    frames = load_frames_as_canvases(path)
    first_stats = analyze_canvas(frames[0])
    warnings: list[str] = []
    if len(frames) > 1:
        frame_stats = [analyze_canvas(f) for f in frames]
        first_stats["frame_count"] = len(frames)
        first_stats["max_islands"] = max(s["islands"] for s in frame_stats)
        min_margins = {
            side: min(s["margins"][side] for s in frame_stats)
            for side in ("top", "right", "bottom", "left")
        }
        first_stats["min_margins"] = min_margins
        dup_count = sum(
            1 for i in range(1, len(frames)) if frames[i].pixels == frames[i - 1].pixels
        )
        first_stats["duplicate_frames"] = dup_count
        for side, val in min_margins.items():
            if val == 0:
                warnings.append(f"Frame touches '{side}' border (min_margins.{side}=0); risk of clipping.")
        if dup_count > 0:
            warnings.append(f"{dup_count} adjacent duplicate frame(s) detected; animation may stutter.")
    else:
        for side, val in first_stats["margins"].items():
            if val == 0:
                warnings.append(f"Sprite touches '{side}' border (margins.{side}=0).")
    if warnings:
        first_stats["warnings"] = warnings
    return first_stats, frames

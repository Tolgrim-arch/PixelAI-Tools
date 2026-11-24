"""Canvas, PNG, and multi-frame GIF inspection & QA linting utilities for AI agents."""

from collections import deque
from pathlib import Path
from typing import Any
from PIL import Image, ImageSequence
from pixelai.canvas import Canvas, bitmap_text_width
from pixelai.color import RGBA, lerp_rgba


def edge_check(canvas: Canvas) -> dict[str, list[list[int]]]:
    """Detect silhouette edge artifacts: 1px nubs, 1px-thin strips, and 1px pinholes."""
    w, h = canvas.width, canvas.height

    def _solid(x: int, y: int) -> int:
        if x < 0 or y < 0 or x >= w or y >= h:
            return 0
        return 1 if canvas.pixels[y * w + x][3] > 0 else 0

    nubs: list[list[int]] = []
    strips: list[list[int]] = []
    holes: list[list[int]] = []
    for y in range(h):
        for x in range(w):
            l = _solid(x - 1, y)
            rt = _solid(x + 1, y)
            u = _solid(x, y - 1)
            d = _solid(x, y + 1)
            n = l + rt + u + d
            if _solid(x, y):
                if n <= 1:
                    nubs.append([x, y])
                elif n == 2 and ((l and rt) or (u and d)):
                    strips.append([x, y])
            elif 0 < x < w - 1 and 0 < y < h - 1 and n >= 3:
                holes.append([x, y])
    return {"nubs": nubs, "strips": strips, "holes": holes}


def render_ruler(
    canvas: Canvas,
    scale: int = 4,
    step: int = 8,
    bg: RGBA = (22, 22, 26, 255),
    ink: RGBA = (235, 235, 235, 255),
    line: RGBA = (255, 90, 160, 255),
) -> Canvas:
    """Render an upscaled diagnostic canvas with numbered pixel-coordinate gridlines."""
    s = max(1, int(scale))
    grid_step = max(1, int(step))
    ml = bitmap_text_width(str(max(canvas.width, canvas.height)), scale=1) + 4
    mt = 9
    out_w = canvas.width * s + ml + 1
    out_h = canvas.height * s + mt + 1
    out = Canvas(out_w, out_h, fill=bg)
    k1: RGBA = (44, 44, 50, 255)
    k2: RGBA = (36, 36, 42, 255)

    for j in range(canvas.height * s):
        sy = j // s
        for i in range(canvas.width * s):
            sx = i // s
            px = canvas.get_pixel(sx, sy)
            col = px if px[3] > 0 else (k1 if ((i >> 3) ^ (j >> 3)) & 1 else k2)
            out.pixels[(mt + j) * out_w + ml + i] = col

    def _tint(x: int, y: int) -> None:
        if out.in_bounds(x, y):
            idx = y * out_w + x
            out.pixels[idx] = lerp_rgba(out.pixels[idx], line, 0.55)

    for gx in range(0, canvas.width + 1, grid_step):
        lx = ml + gx * s
        for y in range(max(0, mt - 2), out_h):
            _tint(lx, y)
        out.draw_bitmap_text(lx + 2, 1, str(gx), ink, scale=1)

    for gy in range(0, canvas.height + 1, grid_step):
        ly = mt + gy * s
        for x in range(max(0, ml - 2), out_w):
            _tint(x, ly)
        out.draw_bitmap_text(1, ly + 2, str(gy), ink, scale=1)

    return out


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
    """Compute bounding box, margins, opaque pixel count, unique colors, islands, and edge quality."""
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
            "isolated_single_pixels": 0,
            "edge_quality": {"nubs": 0, "strips": 0, "holes": 0},
            "bbox": None,
            "margins": {"top": canvas.height, "right": canvas.width, "bottom": canvas.height, "left": canvas.width},
        }

    isolated_singles = 0
    for y in range(canvas.height):
        for x in range(canvas.width):
            if canvas.get_pixel(x, y)[3] > 0:
                has_neighbor = any(
                    canvas.in_bounds(x + dx, y + dy) and canvas.get_pixel(x + dx, y + dy)[3] > 0
                    for dy in (-1, 0, 1)
                    for dx in (-1, 0, 1)
                    if not (dx == 0 and dy == 0)
                )
                if not has_neighbor:
                    isolated_singles += 1

    edges = edge_check(canvas)
    return {
        "width": canvas.width,
        "height": canvas.height,
        "opaque_pixels": opaque,
        "unique_colors": len(colors),
        "color_histogram": color_histogram(canvas, top_n=12),
        "islands": count_connected_components(canvas),
        "isolated_single_pixels": isolated_singles,
        "edge_quality": {
            "nubs": len(edges["nubs"]),
            "strips": len(edges["strips"]),
            "holes": len(edges["holes"]),
        },
        "bbox": {"x": min_x, "y": min_y, "w": max_x - min_x + 1, "h": max_y - min_y + 1},
        "margins": {
            "top": min_y,
            "right": canvas.width - 1 - max_x,
            "bottom": canvas.height - 1 - max_y,
            "left": min_x,
        },
    }


def color_histogram(canvas: Canvas, top_n: int = 12) -> list[dict[str, Any]]:
    """Return top-N opaque colors sorted by frequency with hex code, pixel count, and share."""
    counts: dict[RGBA, int] = {}
    total = 0
    for px in canvas.pixels:
        if px[3] > 0:
            counts[px] = counts.get(px, 0) + 1
            total += 1
    if total == 0:
        return []
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)[: max(1, top_n)]
    return [
        {
            "hex": f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}" if c[3] == 255 else f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}{c[3]:02x}",
            "count": n,
            "share": round(n / total, 4),
        }
        for c, n in ranked
    ]


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
        total_px = max(1, frames[0].width * frames[0].height)
        deltas = [
            round(
                sum(1 for a, b in zip(frames[i - 1].pixels, frames[i].pixels) if a != b) / total_px,
                4,
            )
            for i in range(1, len(frames))
        ]
        first_stats["frame_deltas"] = deltas
        first_stats["avg_frame_delta"] = round(sum(deltas) / len(deltas), 4) if deltas else 0.0
        first_stats["max_frame_delta"] = max(deltas) if deltas else 0.0
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


def _blit_checker(dst: Canvas, src: Canvas, ox: int, oy: int, scale: int) -> None:
    k1: RGBA = (44, 44, 52, 255)
    k2: RGBA = (36, 36, 44, 255)
    sw, sh = src.width * scale, src.height * scale
    for j in range(sh):
        sy = j // scale
        for i in range(sw):
            sx = i // scale
            px = src.get_pixel(sx, sy)
            col = px if px[3] > 0 else (k1 if ((i >> 3) ^ (j >> 3)) & 1 else k2)
            dst.set_pixel(ox + i, oy + j, col)


def diff_canvases(before: Canvas, after: Canvas) -> tuple[dict[str, Any], Canvas]:
    """Compare two canvases pixel-by-pixel and return metrics plus a diff highlight canvas."""
    w = max(before.width, after.width)
    h = max(before.height, after.height)
    diff_c = Canvas(w, h)
    changed = 0
    min_x, min_y = w, h
    max_x, max_y = -1, -1

    for y in range(h):
        for x in range(w):
            a = before.get_pixel(x, y) if before.in_bounds(x, y) else (0, 0, 0, 0)
            b = after.get_pixel(x, y) if after.in_bounds(x, y) else (0, 0, 0, 0)
            if a != b:
                changed += 1
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
                # Green = added, Red = removed, Magenta = modified
                if a[3] == 0 and b[3] > 0:
                    diff_c.set_pixel(x, y, (80, 235, 130, 255))
                elif a[3] > 0 and b[3] == 0:
                    diff_c.set_pixel(x, y, (240, 75, 85, 255))
                else:
                    diff_c.set_pixel(x, y, (255, 80, 200, 255))
            elif b[3] > 0:
                # Dim unchanged silhouette for spatial context
                diff_c.set_pixel(x, y, (b[0] // 3, b[1] // 3, b[2] // 3, 255))

    total = max(1, w * h)
    stats: dict[str, Any] = {
        "same_size": (before.width == after.width and before.height == after.height),
        "before_size": [before.width, before.height],
        "after_size": [after.width, after.height],
        "changed_pixels": changed,
        "total_pixels": w * h,
        "change_ratio": round(changed / total, 4),
        "change_bbox": (
            {"x": min_x, "y": min_y, "w": max_x - min_x + 1, "h": max_y - min_y + 1}
            if changed > 0
            else None
        ),
    }
    return stats, diff_c


def render_diff_sheet(before: Canvas, after: Canvas, scale: int = 4) -> tuple[dict[str, Any], Canvas]:
    """Render a BEFORE | AFTER | DIFF side-by-side comparison sheet with metrics."""
    s = max(1, int(scale))
    stats, diff_c = diff_canvases(before, after)
    pad = 6
    label_h = 10
    bw, bh = before.width * s, before.height * s
    aw, ah = after.width * s, after.height * s
    dw, dh = diff_c.width * s, diff_c.height * s
    out_w = pad * 4 + bw + aw + dw
    out_h = pad * 2 + label_h + max(bh, ah, dh)
    out = Canvas(out_w, out_h, fill=(22, 22, 28, 255))

    out.draw_bitmap_text(pad, pad, "BEFORE", (235, 235, 240, 255), scale=1)
    out.draw_bitmap_text(pad * 2 + bw, pad, "AFTER", (140, 235, 170, 255), scale=1)
    out.draw_bitmap_text(pad * 3 + bw + aw, pad, "DIFF", (255, 110, 210, 255), scale=1)

    oy = pad + label_h
    _blit_checker(out, before, pad, oy, s)
    _blit_checker(out, after, pad * 2 + bw, oy, s)
    _blit_checker(out, diff_c, pad * 3 + bw + aw, oy, s)
    return stats, out


def render_contact_sheet(
    frames: list[Canvas],
    names: list[str] | None = None,
    scale: int = 4,
    cols: int | None = None,
) -> Canvas:
    """Render all animation frames onto a labeled checkerboard contact sheet."""
    if not frames:
        raise ValueError("Cannot render contact sheet from empty frames list")
    s = max(1, int(scale))
    n = len(frames)
    c_count = max(1, min(cols if cols is not None else min(6, n), n))
    r_count = (n + c_count - 1) // c_count
    fw = max(f.width for f in frames) * s
    fh = max(f.height for f in frames) * s
    pad = 6
    label_h = 9
    cell_w = max(fw, 24)
    cell_h = fh + label_h
    out_w = pad + c_count * (cell_w + pad)
    out_h = pad + r_count * (cell_h + pad)
    out = Canvas(out_w, out_h, fill=(22, 22, 28, 255))

    for idx, frame in enumerate(frames):
        col = idx % c_count
        row = idx // c_count
        ox = pad + col * (cell_w + pad)
        oy = pad + row * (cell_h + pad)
        label = (names[idx] if names and idx < len(names) else f"F{idx}").upper()[:10]
        out.draw_bitmap_text(ox, oy, label, (235, 235, 240, 255), scale=1)
        _blit_checker(out, frame, ox, oy + label_h, s)
    return out


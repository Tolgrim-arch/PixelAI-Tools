"""Reference image ingestion: fractional pixel-grid recovery, de-JPEG resampling,
OKLAB perceptual color quantization, and background removal.

Supports JPG, JPEG, JFIF, PNG, and WEBP reference images (such as Pinterest/X saves)
and reconstructs clean 1:1 native pixel art canvases for style study.
"""

from __future__ import annotations

import math
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from pixelai.canvas import Canvas
from pixelai.color import RGBA, TRANSPARENT

SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".jfif", ".png", ".webp"}


@dataclass(frozen=True)
class GridEstimate:
    """Detected logical pixel grid in an upscaled or native reference image."""

    cell_w: float
    cell_h: float
    offset_x: float
    offset_y: float
    grid_w: int
    grid_h: int
    confidence: float


@dataclass
class IngestResult:
    """Result of ingesting a reference image into a clean 1:1 native Canvas."""

    canvas: Canvas
    source_size: tuple[int, int]
    grid: GridEstimate
    palette: list[RGBA]
    bg_removed: bool
    bg_color: RGBA | None


# ---------------------------------------------------------------------------
# Fast pure-Python OKLAB color space (perceptually uniform for pixel art)
# ---------------------------------------------------------------------------

def _srgb_to_linear(c: int) -> float:
    v = c / 255.0
    if v <= 0.04045:
        return v / 12.92
    return ((v + 0.055) / 1.055) ** 2.4


def rgb_to_oklab(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert 8-bit sRGB to perceptual OKLAB (L in [0,1], a/b roughly [-0.4,0.4])."""
    lr = _srgb_to_linear(r)
    lg = _srgb_to_linear(g)
    lb = _srgb_to_linear(b)

    l_ = 0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb
    m_ = 0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb
    s_ = 0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb

    l_c = l_ ** (1.0 / 3.0) if l_ > 0.0 else 0.0
    m_c = m_ ** (1.0 / 3.0) if m_ > 0.0 else 0.0
    s_c = s_ ** (1.0 / 3.0) if s_ > 0.0 else 0.0

    L = 0.2104542553 * l_c + 0.7936177850 * m_c - 0.0040720468 * s_c
    a = 1.9779984951 * l_c - 2.4285922050 * m_c + 0.4505937099 * s_c
    b_ = 0.0259040371 * l_c + 0.7827717662 * m_c - 0.8086757660 * s_c
    return (L, a, b_)


def oklab_dist_sq(c1: tuple[float, float, float], c2: tuple[float, float, float]) -> float:
    dL = c1[0] - c2[0]
    da = c1[1] - c2[1]
    db = c1[2] - c2[2]
    return dL * dL + da * da + db * db


def rgb_oklab_dist(a: RGBA, b: RGBA) -> float:
    return math.sqrt(oklab_dist_sq(rgb_to_oklab(a[0], a[1], a[2]), rgb_to_oklab(b[0], b[1], b[2])))


# ---------------------------------------------------------------------------
# Fractional Pixel-Grid Detection (handles Pinterest 736px non-integer scales)
# ---------------------------------------------------------------------------

def _edge_profiles(img: Image.Image) -> tuple[list[float], list[float]]:
    """Compute 1D horizontal (column-boundary) and vertical (row-boundary) edge energy."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    data = list(rgb.getdata())

    # Stride sampling for speed on large images while keeping full 1px resolution along the axis
    row_step = max(1, h // 180)
    col_step = max(1, w // 180)

    col_energy = [0.0] * max(0, w - 1)
    for y in range(0, h, row_step):
        row_off = y * w
        for x in range(w - 1):
            p0 = data[row_off + x]
            p1 = data[row_off + x + 1]
            col_energy[x] += abs(p1[0] - p0[0]) + abs(p1[1] - p0[1]) + abs(p1[2] - p0[2])

    row_energy = [0.0] * max(0, h - 1)
    for y in range(h - 1):
        r0 = y * w
        r1 = (y + 1) * w
        acc = 0.0
        for x in range(0, w, col_step):
            p0 = data[r0 + x]
            p1 = data[r1 + x]
            acc += abs(p1[0] - p0[0]) + abs(p1[1] - p0[1]) + abs(p1[2] - p0[2])
        row_energy[y] = acc

    return col_energy, row_energy


def _score_period(energy: list[float], period: float) -> tuple[float, float]:
    """Score a candidate grid period by boundary-vs-center energy contrast.

    For a true pixel pitch `p`, edges concentrate at `offset + k*p` while cell
    interiors at `offset + (k + 0.5)*p` are flat (near-zero energy). Even
    harmonics (2p, 4p) place their centers on real boundaries and score ~0.
    """
    n = len(energy)
    if n < 8 or period < 1.5:
        return 0.0, 0.0
    mean_e = sum(energy) / n
    if mean_e <= 1e-6:
        return 0.0, 0.0

    steps = max(6, min(20, int(round(period * 2))))
    best_score = -1.0
    best_offset = 0.0
    half = period * 0.5

    for s in range(steps):
        off = (s / steps) * period
        pos = off
        hits = 0
        boundary_sum = 0.0
        center_sum = 0.0
        while pos + half < n - 1:
            b_idx = int(round(pos))
            c_idx = int(round(pos + half))
            if 0 <= b_idx < n and 0 <= c_idx < n:
                boundary_sum += energy[b_idx]
                center_sum += energy[c_idx]
                hits += 1
            pos += period
        if hits >= 4:
            b_avg = boundary_sum / hits
            c_avg = center_sum / hits
            # Normalized contrast: high at boundaries, low at centers
            score = (b_avg - c_avg) / mean_e
            if score > best_score:
                best_score = score
                best_offset = off
    return best_score, best_offset


def detect_pixel_grid(img: Image.Image, force_scale: float | None = None) -> GridEstimate:
    """Detect square logical pixel size (supports non-integer scales like 11.5px on 736px Pinterest saves)."""
    w, h = img.size
    if force_scale is not None and force_scale > 0:
        cw = float(force_scale)
        gw = max(1, int(round(w / cw)))
        gh = max(1, int(round(h / cw)))
        return GridEstimate(cw, cw, 0.0, 0.0, gw, gh, 1.0)

    # Already small native sprite
    if w <= 64 and h <= 64:
        return GridEstimate(1.0, 1.0, 0.0, 0.0, w, h, 1.0)

    col_e, row_e = _edge_profiles(img)
    min_dim = min(w, h)
    max_p = min(24.0, min_dim / 16.0)
    if max_p < 2.0:
        return GridEstimate(1.0, 1.0, 0.0, 0.0, w, h, 1.0)

    # Joint square-pixel search across both X and Y axes
    candidates: list[tuple[float, float, float, float]] = []
    p = 2.0
    while p <= max_p:
        sx, ox = _score_period(col_e, p)
        sy, oy = _score_period(row_e, p)
        joint = 0.5 * (sx + sy)
        candidates.append((joint, p, ox, oy))
        p += 0.25

    if not candidates:
        return GridEstimate(1.0, 1.0, 0.0, 0.0, w, h, 0.0)

    best_score, best_p, best_ox, best_oy = max(candidates, key=lambda t: t[0])

    # Guard against odd harmonics (3x)
    for div in (2.0, 3.0):
        sub_p = best_p / div
        if sub_p >= 2.0:
            sx, ox = _score_period(col_e, sub_p)
            sy, oy = _score_period(row_e, sub_p)
            sub_joint = 0.5 * (sx + sy)
            if sub_joint >= best_score * 0.80:
                best_score, best_p, best_ox, best_oy = sub_joint, sub_p, ox, oy

    # Sub-pixel refinement around best_p
    for delta in (-0.20, -0.15, -0.10, -0.05, 0.05, 0.10, 0.15, 0.20):
        cand_p = best_p + delta
        if cand_p >= 1.8:
            sx, ox = _score_period(col_e, cand_p)
            sy, oy = _score_period(row_e, cand_p)
            joint = 0.5 * (sx + sy)
            if joint > best_score:
                best_score, best_p, best_ox, best_oy = joint, cand_p, ox, oy

    # Weak periodicity -> already 1:1 or smooth illustration
    if best_score < 0.25:
        if max(w, h) > 256:
            scale = max(w, h) / 128.0
            return GridEstimate(
                round(scale, 3),
                round(scale, 3),
                0.0,
                0.0,
                max(1, int(round(w / scale))),
                max(1, int(round(h / scale))),
                0.25,
            )
        return GridEstimate(1.0, 1.0, 0.0, 0.0, w, h, 0.25)

    gw = max(1, int(round((w - best_ox) / best_p)))
    gh = max(1, int(round((h - best_oy) / best_p)))
    confidence = min(1.0, max(0.0, best_score / 1.5))

    return GridEstimate(
        cell_w=round(best_p, 3),
        cell_h=round(best_p, 3),
        offset_x=round(best_ox, 3),
        offset_y=round(best_oy, 3),
        grid_w=gw,
        grid_h=gh,
        confidence=round(confidence, 3),
    )


# ---------------------------------------------------------------------------
# De-JPEG Cell-Center Resampling
# ---------------------------------------------------------------------------

def resample_to_native_grid(img: Image.Image, grid: GridEstimate) -> Canvas:
    """Resample an upscaled/JPEG image onto its 1:1 logical pixel grid using inner-cell medians."""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    canvas = Canvas(grid.grid_w, grid.grid_h)

    if grid.cell_w <= 1.05 and grid.cell_h <= 1.05:
        for y in range(min(h, grid.grid_h)):
            for x in range(min(w, grid.grid_w)):
                r, g, b, a = px[x, y]
                canvas.set_pixel(x, y, (r, g, b, 255 if a >= 128 else 0))
        return canvas

    # Sample inner 50% core of each cell to avoid JPEG ringing at cell boundaries
    margin_x = grid.cell_w * 0.25
    margin_y = grid.cell_h * 0.25

    for gy in range(grid.grid_h):
        y0 = max(0, int(math.floor(grid.offset_y + gy * grid.cell_h + margin_y)))
        y1 = min(h - 1, int(math.ceil(grid.offset_y + (gy + 1) * grid.cell_h - margin_y)))
        if y1 < y0:
            y0 = y1 = max(0, min(h - 1, int(round(grid.offset_y + (gy + 0.5) * grid.cell_h))))

        for gx in range(grid.grid_w):
            x0 = max(0, int(math.floor(grid.offset_x + gx * grid.cell_w + margin_x)))
            x1 = min(w - 1, int(math.ceil(grid.offset_x + (gx + 1) * grid.cell_w - margin_x)))
            if x1 < x0:
                x0 = x1 = max(0, min(w - 1, int(round(grid.offset_x + (gx + 0.5) * grid.cell_w))))

            rs: list[int] = []
            gs: list[int] = []
            bs: list[int] = []
            alphas: list[int] = []
            for sy in range(y0, y1 + 1):
                for sx in range(x0, x1 + 1):
                    r, g, b, a = px[sx, sy]
                    rs.append(r)
                    gs.append(g)
                    bs.append(b)
                    alphas.append(a)

            alphas.sort()
            med_a = alphas[len(alphas) // 2]
            if med_a < 128:
                canvas.set_pixel(gx, gy, TRANSPARENT)
            else:
                rs.sort()
                gs.sort()
                bs.sort()
                mid = len(rs) // 2
                canvas.set_pixel(gx, gy, (rs[mid], gs[mid], bs[mid], 255))

    return canvas


# ---------------------------------------------------------------------------
# Background Detection & Flood-Fill Removal (for JPG/JFIF/WEBP without alpha)
# ---------------------------------------------------------------------------

def remove_background(canvas: Canvas, tolerance: float = 0.075) -> tuple[bool, RGBA | None]:
    """Detect solid/noised border background and flood-fill it to transparent.

    If the canvas already has >= 5% transparent pixels, preserves existing alpha.
    """
    total = canvas.width * canvas.height
    if total == 0:
        return False, None

    transparent_count = sum(1 for c in canvas.pixels if c[3] == 0)
    if transparent_count / total >= 0.05:
        return False, None

    # Sample border pixels
    border: list[RGBA] = []
    for x in range(canvas.width):
        border.append(canvas.get_pixel(x, 0))
        border.append(canvas.get_pixel(x, canvas.height - 1))
    for y in range(1, canvas.height - 1):
        border.append(canvas.get_pixel(0, y))
        border.append(canvas.get_pixel(canvas.width - 1, y))

    if not border:
        return False, None

    # Bucket border colors coarsely (4-bit per channel) to find dominant background even with JPEG noise
    buckets: Counter[tuple[int, int, int]] = Counter()
    bucket_samples: dict[tuple[int, int, int], list[RGBA]] = {}
    for c in border:
        key = (c[0] >> 4, c[1] >> 4, c[2] >> 4)
        buckets[key] += 1
        bucket_samples.setdefault(key, []).append(c)

    top_key, top_count = buckets.most_common(1)[0]
    if top_count / len(border) < 0.35:
        # Full-bleed scene / tileset without a clear uniform background
        return False, None

    samples = bucket_samples[top_key]
    bg_color: RGBA = (
        sorted(c[0] for c in samples)[len(samples) // 2],
        sorted(c[1] for c in samples)[len(samples) // 2],
        sorted(c[2] for c in samples)[len(samples) // 2],
        255,
    )
    bg_lab = rgb_to_oklab(bg_color[0], bg_color[1], bg_color[2])
    tol_sq = tolerance * tolerance

    visited = [[False] * canvas.width for _ in range(canvas.height)]
    q: deque[tuple[int, int]] = deque()

    def _try_enqueue(x: int, y: int) -> None:
        if visited[y][x]:
            return
        c = canvas.get_pixel(x, y)
        if c[3] == 0:
            visited[y][x] = True
            return
        if oklab_dist_sq(rgb_to_oklab(c[0], c[1], c[2]), bg_lab) <= tol_sq:
            visited[y][x] = True
            q.append((x, y))

    for x in range(canvas.width):
        _try_enqueue(x, 0)
        _try_enqueue(x, canvas.height - 1)
    for y in range(1, canvas.height - 1):
        _try_enqueue(0, y)
        _try_enqueue(canvas.width - 1, y)

    removed = 0
    while q:
        cx, cy = q.popleft()
        canvas.set_pixel(cx, cy, TRANSPARENT)
        removed += 1
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if 0 <= nx < canvas.width and 0 <= ny < canvas.height:
                _try_enqueue(nx, ny)

    return removed > 0, bg_color if removed > 0 else None


# ---------------------------------------------------------------------------
# Perceptual OKLAB Quantization (collapses JPEG/WEBP artifact colors)
# ---------------------------------------------------------------------------

def quantize_oklab(
    canvas: Canvas,
    max_colors: int = 32,
    merge_threshold: float = 0.045,
) -> list[RGBA]:
    """Snap noisy JPEG/WEBP colors into a clean perceptual palette in OKLAB."""
    counts: Counter[RGBA] = Counter(c for c in canvas.pixels if c[3] > 0)
    if not counts:
        return []

    # Sort by frequency descending so dominant artist colors become cluster anchors
    ordered = counts.most_common()
    labs = {c: rgb_to_oklab(c[0], c[1], c[2]) for c, _ in ordered}

    clusters: list[dict] = []
    thresh_sq = merge_threshold * merge_threshold

    for color, cnt in ordered:
        lab = labs[color]
        best_idx = -1
        best_d = thresh_sq
        for i, cl in enumerate(clusters):
            d = oklab_dist_sq(lab, cl["lab"])
            if d < best_d:
                best_d = d
                best_idx = i
        if best_idx >= 0:
            cl = clusters[best_idx]
            cl["count"] += cnt
            # Keep anchor color as the most frequent member (crisp pixel art, no muddy averaging)
        else:
            clusters.append({"anchor": color, "lab": lab, "count": cnt})

    # If still above max_colors, greedily merge the least-frequent cluster into its nearest neighbor
    while len(clusters) > max_colors:
        clusters.sort(key=lambda cl: cl["count"])
        smallest = clusters.pop(0)
        best_target = min(
            clusters,
            key=lambda cl: oklab_dist_sq(smallest["lab"], cl["lab"]),
        )
        best_target["count"] += smallest["count"]

    # Sort final palette by frequency descending
    clusters.sort(key=lambda cl: cl["count"], reverse=True)
    palette = [cl["anchor"] for cl in clusters]
    pal_labs = [cl["lab"] for cl in clusters]

    # Map every opaque pixel to its nearest palette anchor in OKLAB
    remap: dict[RGBA, RGBA] = {}
    for color in counts:
        lab = labs[color]
        best_i = min(range(len(palette)), key=lambda i: oklab_dist_sq(lab, pal_labs[i]))
        remap[color] = palette[best_i]

    for i, c in enumerate(canvas.pixels):
        if c[3] > 0:
            canvas.pixels[i] = remap[c]

    return palette


# ---------------------------------------------------------------------------
# End-to-End Ingestion Entrypoint
# ---------------------------------------------------------------------------

def ingest_reference_image(
    path: str | Path,
    *,
    force_scale: float | None = None,
    max_colors: int = 32,
    keep_bg: bool = False,
    merge_threshold: float = 0.045,
) -> IngestResult:
    """Load a JPG/JFIF/PNG/WEBP reference image and recover a clean 1:1 pixel art Canvas."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Reference image not found: {p}")
    img = Image.open(p)
    source_size = img.size

    grid = detect_pixel_grid(img, force_scale=force_scale)
    canvas = resample_to_native_grid(img, grid)

    bg_removed = False
    bg_color = None
    if not keep_bg:
        bg_removed, bg_color = remove_background(canvas)

    palette = quantize_oklab(canvas, max_colors=max_colors, merge_threshold=merge_threshold)
    return IngestResult(
        canvas=canvas,
        source_size=source_size,
        grid=grid,
        palette=palette,
        bg_removed=bg_removed,
        bg_color=bg_color,
    )

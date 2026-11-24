"""Style DNA extraction and multi-reference consolidation (Workflow A).

Analyzes clean 1:1 native pixel art canvases (or raw JPG/JFIF/PNG/WEBP references
via `style_ingest`) and produces a declarative `.style.json` profile capturing:
- Color palette & shading ramps with measured hue-shifting
- Outline style (ext_outline, selout, or lineless) and contrast
- Dominant lighting direction and rim-light presence
- Shading texture (dithering ratio, cluster cleanliness)
- Proportions and explicit AI-agent authoring rules
"""

from __future__ import annotations

import colorsys
import math
from collections import Counter
from pathlib import Path
from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import RGBA, luminance
from pixelai.style_ingest import (
    SUPPORTED_IMAGE_EXTS,
    IngestResult,
    ingest_reference_image,
    rgb_to_oklab,
)

STYLE_SCHEMA_VERSION = "1.0"


def _rgba_to_hex(c: RGBA) -> str:
    return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"


def _hex_to_rgba(h: str) -> RGBA:
    s = h.strip().lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


def _rgb_to_hsl_deg(c: RGBA) -> tuple[float, float, float]:
    """Return (hue_deg [0..360), sat [0..1], light [0..1])."""
    h, l, s = colorsys.rgb_to_hls(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    return (h * 360.0, s, l)


def _hue_diff_deg(h1: float, h2: float) -> float:
    """Signed shortest angular difference h2 - h1 in [-180, 180]."""
    d = (h2 - h1 + 180.0) % 360.0 - 180.0
    return d


# ---------------------------------------------------------------------------
# Ramp Extraction & Hue-Shift Analysis
# ---------------------------------------------------------------------------

def extract_ramps(palette: list[RGBA]) -> dict[str, Any]:
    """Group palette colors into shading ramps and measure shadow/highlight hue-shifting."""
    if not palette:
        return {
            "ramps": [],
            "shadow_hue_shift_deg": 0.0,
            "highlight_hue_shift_deg": 0.0,
            "avg_saturation": 0.0,
            "luminance_span": 0.0,
        }

    # Separate near-achromatic (neutrals/ink/white) from chromatic colors
    neutrals: list[RGBA] = []
    chromatics: list[tuple[RGBA, float, float, float]] = []
    sats: list[float] = []
    lums: list[float] = []

    for c in palette:
        h, s, l = _rgb_to_hsl_deg(c)
        sats.append(s)
        lums.append(luminance(c) / 255.0)
        if s < 0.14 or l < 0.10 or l > 0.93:
            neutrals.append(c)
        else:
            chromatics.append((c, h, s, l))

    # Cluster chromatic colors by hue proximity (within 38 degrees)
    chromatics.sort(key=lambda t: t[1])
    groups: list[list[tuple[RGBA, float, float, float]]] = []
    for item in chromatics:
        placed = False
        for g in groups:
            avg_h = g[0][1]
            if abs(_hue_diff_deg(avg_h, item[1])) <= 38.0:
                g.append(item)
                placed = True
                break
        if not placed:
            groups.append([item])

    ramps: list[dict[str, Any]] = []
    shadow_shifts: list[float] = []
    highlight_shifts: list[float] = []

    if neutrals:
        neutrals_sorted = sorted(neutrals, key=luminance)
        ramps.append({
            "name": "neutral",
            "colors": [_rgba_to_hex(c) for c in neutrals_sorted],
            "hue_shift_deg": 0.0,
        })

    for idx, g in enumerate(groups):
        g_sorted = sorted(g, key=lambda t: luminance(t[0]))
        cols = [t[0] for t in g_sorted]
        hues = [t[1] for t in g_sorted]
        if len(hues) >= 2:
            mid_i = len(hues) // 2
            sh_shift = _hue_diff_deg(hues[mid_i], hues[0])
            hi_shift = _hue_diff_deg(hues[mid_i], hues[-1])
            shadow_shifts.append(sh_shift)
            highlight_shifts.append(hi_shift)
            total_shift = round(_hue_diff_deg(hues[0], hues[-1]), 1)
        else:
            total_shift = 0.0
        ramps.append({
            "name": f"ramp_{idx + 1}",
            "colors": [_rgba_to_hex(c) for c in cols],
            "hue_shift_deg": total_shift,
        })

    return {
        "ramps": ramps,
        "shadow_hue_shift_deg": round(sum(shadow_shifts) / len(shadow_shifts), 1) if shadow_shifts else 0.0,
        "highlight_hue_shift_deg": round(sum(highlight_shifts) / len(highlight_shifts), 1) if highlight_shifts else 0.0,
        "avg_saturation": round(sum(sats) / len(sats), 3),
        "luminance_span": round(max(lums) - min(lums), 3) if lums else 0.0,
    }


# ---------------------------------------------------------------------------
# Outline, Lighting, Shading, and Proportion Analyzers
# ---------------------------------------------------------------------------

def analyze_outline(canvas: Canvas) -> dict[str, Any]:
    """Classify external outline style (ext_outline, selout, or lineless) and measure contrast."""
    w, h = canvas.width, canvas.height
    border_pixels: list[RGBA] = []
    interior_pixels: list[RGBA] = []

    for y in range(h):
        for x in range(w):
            c = canvas.get_pixel(x, y)
            if c[3] == 0:
                continue
            touches_transparent = False
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if nx < 0 or nx >= w or ny < 0 or ny >= h or canvas.get_pixel(nx, ny)[3] == 0:
                    touches_transparent = True
                    break
            if touches_transparent:
                border_pixels.append(c)
            else:
                interior_pixels.append(c)

    if not border_pixels:
        return {
            "mode": "ext_outline",
            "color": "#1c141d",
            "contrast": 0.0,
            "border_unique_colors": 0,
        }

    border_counts = Counter(border_pixels)
    top_border_color, top_border_cnt = border_counts.most_common(1)[0]
    top_share = top_border_cnt / len(border_pixels)

    avg_border_lum = sum(luminance(c) for c in border_pixels) / len(border_pixels)
    avg_interior_lum = (
        sum(luminance(c) for c in interior_pixels) / len(interior_pixels)
        if interior_pixels
        else avg_border_lum
    )
    contrast = round((avg_interior_lum - avg_border_lum) / 255.0, 3)

    # Classification:
    # - Uniform dark border (top color >= 55% of border & dark) -> ext_outline
    # - Darkened border with multiple hue-matched colors -> selout
    # - Border not meaningfully darker than interior -> lineless
    if contrast < 0.08 and avg_border_lum > 90:
        mode = "lineless"
    elif top_share >= 0.55 and luminance(top_border_color) < 95:
        mode = "ext_outline"
    elif contrast >= 0.08:
        mode = "selout"
    else:
        mode = "ext_outline" if luminance(top_border_color) < 80 else "lineless"

    return {
        "mode": mode,
        "color": _rgba_to_hex(top_border_color),
        "contrast": contrast,
        "border_unique_colors": len(border_counts),
    }


def analyze_lighting(canvas: Canvas) -> dict[str, Any]:
    """Estimate dominant 2D light direction from luminance gradients inside the silhouette."""
    w, h = canvas.width, canvas.height
    gx_sum = 0.0
    gy_sum = 0.0
    samples = 0

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = canvas.get_pixel(x, y)
            if c[3] == 0:
                continue
            cl = canvas.get_pixel(x - 1, y)
            cr = canvas.get_pixel(x + 1, y)
            cu = canvas.get_pixel(x, y - 1)
            cd = canvas.get_pixel(x, y + 1)
            if cl[3] > 0 and cr[3] > 0:
                # Positive gx means brighter on the right; light vector points toward brighter side
                gx_sum += luminance(cr) - luminance(cl)
                samples += 1
            if cu[3] > 0 and cd[3] > 0:
                gy_sum += luminance(cd) - luminance(cu)
                samples += 1

    mag = math.hypot(gx_sum, gy_sum)
    if mag < 1e-3 or samples < 10:
        lx, ly = -0.7, -0.7
    else:
        lx, ly = gx_sum / mag, gy_sum / mag

    # Human-readable direction label
    horiz = "left" if lx < -0.3 else ("right" if lx > 0.3 else "")
    vert = "top" if ly < -0.3 else ("bottom" if ly > 0.3 else "")
    label = "_".join(p for p in (vert, horiz) if p) or "top_left"

    return {
        "direction": label,
        "vector": [round(lx, 3), round(ly, 3)],
    }


def analyze_shading(canvas: Canvas) -> dict[str, Any]:
    """Measure dithering frequency and cluster cleanliness."""
    w, h = canvas.width, canvas.height
    opaque = 0
    checker_hits = 0
    isolated = 0

    for y in range(h):
        for x in range(w):
            c = canvas.get_pixel(x, y)
            if c[3] == 0:
                continue
            opaque += 1
            same_n = 0
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and canvas.get_pixel(nx, ny) == c:
                    same_n += 1
            if same_n == 0:
                isolated += 1
            # 2x2 checkerboard dither pattern: (x,y)==(x+1,y+1) and (x+1,y)==(x,y+1) and c != (x+1,y)
            if x + 1 < w and y + 1 < h:
                c_r = canvas.get_pixel(x + 1, y)
                c_d = canvas.get_pixel(x, y + 1)
                c_dr = canvas.get_pixel(x + 1, y + 1)
                if c_r[3] > 0 and c_d[3] > 0 and c_dr[3] > 0:
                    if c == c_dr and c_r == c_d and c != c_r:
                        checker_hits += 1

    if opaque == 0:
        return {"dither_ratio": 0.0, "isolated_pixel_ratio": 0.0, "style": "cel_clean"}

    dither_ratio = checker_hits / opaque
    iso_ratio = isolated / opaque
    shading_style = "dithered" if dither_ratio >= 0.03 else "cel_clean"
    return {
        "dither_ratio": round(dither_ratio, 4),
        "isolated_pixel_ratio": round(iso_ratio, 4),
        "style": shading_style,
    }


def analyze_proportions(canvas: Canvas) -> dict[str, Any]:
    """Measure bounding box aspect ratio and silhouette fill ratio."""
    w, h = canvas.width, canvas.height
    min_x, min_y = w, h
    max_x, max_y = -1, -1
    opaque = 0

    for y in range(h):
        for x in range(w):
            if canvas.get_pixel(x, y)[3] > 0:
                opaque += 1
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

    if max_x < min_x:
        return {"native_size": [w, h], "bbox_aspect": 1.0, "fill_ratio": 0.0}

    bw = max_x - min_x + 1
    bh = max_y - min_y + 1
    return {
        "native_size": [w, h],
        "bbox_size": [bw, bh],
        "bbox_aspect": round(bw / max(1, bh), 3),
        "fill_ratio": round(opaque / max(1, bw * bh), 3),
    }


# ---------------------------------------------------------------------------
# Study & Merge APIs
# ---------------------------------------------------------------------------

def build_agent_rules(profile: dict[str, Any]) -> list[str]:
    """Generate concise, unambiguous authoring rules for AI agents."""
    outline = profile["outline"]
    lighting = profile["lighting"]
    shading = profile["shading"]
    ramps = profile["color_model"]
    pal_count = len(profile["palette"])

    rules = [
        f"Palette discipline: stay near {pal_count} colors using the learned ramps; avoid raw RGB noise.",
        f"Outline style: use '{outline['mode']}' (reference outline color {outline['color']}, contrast {outline['contrast']}).",
        f"Lighting: primary light comes from '{lighting['direction']}' (vector {lighting['vector']}).",
        f"Shading: prefer '{shading['style']}' clusters (dither ratio {shading['dither_ratio']}).",
        f"Hue-shifting: shadow shift {ramps['shadow_hue_shift_deg']}deg, highlight shift {ramps['highlight_hue_shift_deg']}deg.",
        "Layer Z-order (CRITICAL): ops and layers draw BACK-TO-FRONT — index 0 is farthest behind, last index is frontmost (or set explicit integer 'z' on layers: higher z = in front).",
    ]
    return rules


def study_canvas(
    canvas: Canvas,
    palette: list[RGBA],
    *,
    name: str = "learned_style",
    source: str | None = None,
    grid_confidence: float = 1.0,
) -> dict[str, Any]:
    """Extract a complete `.style.json` profile from a single clean 1:1 Canvas."""
    pal_hex = [_rgba_to_hex(c) for c in palette]
    color_model = extract_ramps(palette)
    outline = analyze_outline(canvas)
    lighting = analyze_lighting(canvas)
    shading = analyze_shading(canvas)
    proportions = analyze_proportions(canvas)

    profile: dict[str, Any] = {
        "schema_version": STYLE_SCHEMA_VERSION,
        "name": name,
        "sources": [source] if source else [],
        "confidence": round(grid_confidence, 3),
        "palette": pal_hex,
        "color_model": color_model,
        "outline": outline,
        "lighting": lighting,
        "shading": shading,
        "proportions": proportions,
    }
    profile["agent_rules"] = build_agent_rules(profile)
    return profile


def merge_style_profiles(profiles: list[dict[str, Any]], *, name: str = "merged_style", max_colors: int = 32) -> dict[str, Any]:
    """Consolidate multiple `.style.json` profiles into a single consensus style pack."""
    if not profiles:
        raise ValueError("Cannot merge an empty list of style profiles.")
    if len(profiles) == 1:
        out = dict(profiles[0])
        out["name"] = name
        return out

    # Weight each profile by its grid detection confidence (min 0.2 so nothing is zeroed out)
    weights = [max(0.2, float(p.get("confidence", 0.5))) for p in profiles]
    total_w = sum(weights)

    # Merge palettes using OKLAB clustering to deduplicate near-identical colors across references
    color_votes: list[tuple[RGBA, float]] = []
    for p, w in zip(profiles, weights):
        for rank, hx in enumerate(p.get("palette", [])):
            # Higher weight for more dominant colors in each reference
            color_votes.append((_hex_to_rgba(hx), w / (1.0 + 0.1 * rank)))

    clusters: list[dict[str, Any]] = []
    thresh_sq = 0.055 * 0.055
    for rgba, wt in color_votes:
        lab = rgb_to_oklab(rgba[0], rgba[1], rgba[2])
        best_i = -1
        best_d = thresh_sq
        for i, cl in enumerate(clusters):
            d = (lab[0] - cl["lab"][0]) ** 2 + (lab[1] - cl["lab"][1]) ** 2 + (lab[2] - cl["lab"][2]) ** 2
            if d < best_d:
                best_d = d
                best_i = i
        if best_i >= 0:
            clusters[best_i]["weight"] += wt
        else:
            clusters.append({"rgba": rgba, "lab": lab, "weight": wt})

    clusters.sort(key=lambda cl: cl["weight"], reverse=True)
    merged_palette_rgba = [cl["rgba"] for cl in clusters[:max_colors]]
    merged_palette_hex = [_rgba_to_hex(c) for c in merged_palette_rgba]

    # Consensus outline mode (weighted vote)
    mode_votes: Counter[str] = Counter()
    outline_contrasts = []
    outline_colors = []
    for p, w in zip(profiles, weights):
        ol = p.get("outline", {})
        mode_votes[ol.get("mode", "ext_outline")] += w
        outline_contrasts.append(float(ol.get("contrast", 0.0)) * w)
        if ol.get("color"):
            outline_colors.append((ol["color"], w))

    best_mode = mode_votes.most_common(1)[0][0]
    # Pick darkest weighted outline color
    outline_color = min(outline_colors, key=lambda t: luminance(_hex_to_rgba(t[0])))[0] if outline_colors else "#1c141d"

    # Consensus lighting vector
    lx = sum(float(p.get("lighting", {}).get("vector", [-0.7, -0.7])[0]) * w for p, w in zip(profiles, weights)) / total_w
    ly = sum(float(p.get("lighting", {}).get("vector", [-0.7, -0.7])[1]) * w for p, w in zip(profiles, weights)) / total_w
    lmag = math.hypot(lx, ly) or 1.0
    lx, ly = lx / lmag, ly / lmag
    horiz = "left" if lx < -0.3 else ("right" if lx > 0.3 else "")
    vert = "top" if ly < -0.3 else ("bottom" if ly > 0.3 else "")
    light_label = "_".join(part for part in (vert, horiz) if part) or "top_left"

    # Consensus shading & proportions
    dither_ratio = sum(float(p.get("shading", {}).get("dither_ratio", 0.0)) * w for p, w in zip(profiles, weights)) / total_w
    iso_ratio = sum(float(p.get("shading", {}).get("isolated_pixel_ratio", 0.0)) * w for p, w in zip(profiles, weights)) / total_w
    aspect = sum(float(p.get("proportions", {}).get("bbox_aspect", 1.0)) * w for p, w in zip(profiles, weights)) / total_w
    fill_ratio = sum(float(p.get("proportions", {}).get("fill_ratio", 0.5)) * w for p, w in zip(profiles, weights)) / total_w
    avg_w = int(round(sum(p.get("proportions", {}).get("native_size", [32, 32])[0] * w for p, w in zip(profiles, weights)) / total_w))
    avg_h = int(round(sum(p.get("proportions", {}).get("native_size", [32, 32])[1] * w for p, w in zip(profiles, weights)) / total_w))

    sources: list[str] = []
    for p in profiles:
        for s in p.get("sources", []):
            if s not in sources:
                sources.append(s)

    merged: dict[str, Any] = {
        "schema_version": STYLE_SCHEMA_VERSION,
        "name": name,
        "sources": sources,
        "reference_count": len(profiles),
        "confidence": round(sum(float(p.get("confidence", 0.5)) for p in profiles) / len(profiles), 3),
        "palette": merged_palette_hex,
        "color_model": extract_ramps(merged_palette_rgba),
        "outline": {
            "mode": best_mode,
            "color": outline_color,
            "contrast": round(sum(outline_contrasts) / total_w, 3),
        },
        "lighting": {
            "direction": light_label,
            "vector": [round(lx, 3), round(ly, 3)],
        },
        "shading": {
            "dither_ratio": round(dither_ratio, 4),
            "isolated_pixel_ratio": round(iso_ratio, 4),
            "style": "dithered" if dither_ratio >= 0.03 else "cel_clean",
        },
        "proportions": {
            "native_size": [avg_w, avg_h],
            "bbox_aspect": round(aspect, 3),
            "fill_ratio": round(fill_ratio, 3),
        },
    }
    merged["agent_rules"] = build_agent_rules(merged)
    return merged


def collect_image_paths(inputs: list[str | Path]) -> list[Path]:
    """Expand files and directories into a sorted list of supported reference images."""
    out: list[Path] = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            for child in sorted(p.iterdir()):
                if child.is_file() and child.suffix.lower() in SUPPORTED_IMAGE_EXTS:
                    out.append(child)
        elif p.is_file():
            out.append(p)
        else:
            raise FileNotFoundError(f"Input path not found: {p}")
    return out


def study_reference_images(
    inputs: list[str | Path],
    *,
    name: str = "learned_style",
    max_colors: int = 24,
    force_scale: float | None = None,
    keep_bg: bool = False,
) -> tuple[dict[str, Any], list[tuple[Path, IngestResult]]]:
    """Ingest and study one or more JPG/JFIF/PNG/WEBP references into a `.style.json` profile."""
    paths = collect_image_paths(inputs)
    if not paths:
        raise ValueError("No supported reference images (.jpg, .jpeg, .jfif, .png, .webp) found.")

    ingested: list[tuple[Path, IngestResult]] = []
    profiles: list[dict[str, Any]] = []
    for p in paths:
        res = ingest_reference_image(
            p,
            force_scale=force_scale,
            max_colors=max_colors,
            keep_bg=keep_bg,
        )
        ingested.append((p, res))
        profiles.append(
            study_canvas(
                res.canvas,
                res.palette,
                name=p.stem,
                source=p.name,
                grid_confidence=res.grid.confidence,
            )
        )

    final_profile = (
        profiles[0] if len(profiles) == 1 else merge_style_profiles(profiles, name=name, max_colors=max_colors)
    )
    final_profile["name"] = name
    return final_profile, ingested

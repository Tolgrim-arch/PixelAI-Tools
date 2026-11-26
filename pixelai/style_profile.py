"""Workflow B bridge: load `.style.json` profiles, apply them to specs,
format AI-agent style briefs, and evaluate style fidelity during QA.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from pixelai.canvas import Canvas
from pixelai.color import RGBA, luminance
from pixelai.style_study import analyze_lighting, analyze_outline, analyze_shading

from pixelai.resources import library_root

LIBRARY_STYLES_DIR = library_root() / "styles"


def resolve_style_path(ref: str | Path) -> Path:
    """Resolve a `.style.json` path from a file path, `@styles/<name>`, or `<name>`."""
    s = str(ref).strip()
    p = Path(s)
    if p.is_file():
        return p

    clean = s.removeprefix("@styles/").removesuffix(".style.json").removesuffix(".json")
    for cand in (
        LIBRARY_STYLES_DIR / f"{clean}.style.json",
        LIBRARY_STYLES_DIR / f"{clean}.json",
    ):
        if cand.is_file():
            return cand

    raise FileNotFoundError(
        f"Style profile not found: {ref!r}. Expected a file path or a profile in {LIBRARY_STYLES_DIR}."
    )


def load_style_profile(ref: str | Path) -> dict[str, Any]:
    """Load and validate a `.style.json` profile."""
    path = resolve_style_path(ref)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "palette" not in data:
        raise ValueError(f"Invalid style profile JSON: {path}")
    return data


def build_spec_palette(profile: dict[str, Any]) -> dict[str, str]:
    """Build a deterministic palette dict suitable for JSON specs from a `.style.json`."""
    pal: dict[str, str] = {}
    outline_color = profile.get("outline", {}).get("color")
    if outline_color:
        pal["ink"] = outline_color

    for i, hx in enumerate(profile.get("palette", [])):
        pal[f"s{i}"] = hx

    for ramp in profile.get("color_model", {}).get("ramps", []):
        rname = ramp.get("name", "ramp")
        colors = ramp.get("colors", [])
        for idx, hx in enumerate(colors):
            pal[f"{rname}_{idx}"] = hx

    return pal


def apply_style_to_spec(spec: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Apply a `.style.json` profile to a render spec without clobbering explicit user overrides."""
    out = deepcopy(spec)

    # 1. Merge learned palette keys (preserving explicit user palette keys)
    learned_pal = build_spec_palette(profile)
    existing_pal = out.get("palette")
    if existing_pal is None:
        out["palette"] = learned_pal
    elif isinstance(existing_pal, dict):
        merged = dict(learned_pal)
        merged.update(existing_pal)
        out["palette"] = merged
    # If existing_pal is a named built-in palette string (e.g. "cozy24"), keep it unless user omitted palette.

    # 2. Apply outline style if not explicitly set by the spec
    outline_info = profile.get("outline", {})
    mode = outline_info.get("mode", "ext_outline")
    if "style" not in out:
        out["style"] = "lineless" if mode == "lineless" else "ext_outline"

    # 3. Configure external outline color/selout in `post` if spec has no explicit outline post op
    post = list(out.get("post", []))
    has_outline_post = any(isinstance(op, dict) and op.get("op") == "outline" for op in post)
    if out.get("style") != "lineless" and not has_outline_post:
        ol_color = outline_info.get("color")
        if ol_color:
            post.append({
                "op": "outline",
                "color": ol_color,
                "selout": mode == "selout",
            })
            out["post"] = post

    # 4. Attach style shading context for downstream rigs
    out["_style_context"] = {
        "light_vector": profile.get("lighting", {}).get("vector", [-0.46, -0.62]),
        "shadow_hue_shift_deg": profile.get("color_model", {}).get("shadow_hue_shift_deg", -12.0),
        "highlight_hue_shift_deg": profile.get("color_model", {}).get("highlight_hue_shift_deg", 10.0),
        "outline_mode": mode,
    }

    return out


def format_style_guide(profile: dict[str, Any]) -> str:
    """Format a compact, AI-agent-friendly style brief from a `.style.json` profile."""
    name = profile.get("name", "learned_style")
    sources = profile.get("sources", [])
    outline = profile.get("outline", {})
    lighting = profile.get("lighting", {})
    shading = profile.get("shading", {})
    color_model = profile.get("color_model", {})
    props = profile.get("proportions", {})

    lines = [
        f"# Style Profile: {name}",
        f"- Sources: {len(sources)} reference(s) (confidence: {profile.get('confidence', 1.0)})",
        f"- Outline: `{outline.get('mode', 'ext_outline')}` (color `{outline.get('color', '#1c141d')}`, contrast {outline.get('contrast', 0.0)})",
        f"- Lighting: `{lighting.get('direction', 'top_left')}` (vector {lighting.get('vector', [-0.7, -0.7])})",
        f"- Shading: `{shading.get('style', 'cel_clean')}` (dither_ratio={shading.get('dither_ratio', 0.0)})",
        f"- Hue-Shifting: shadow {color_model.get('shadow_hue_shift_deg', 0.0)}deg | highlight {color_model.get('highlight_hue_shift_deg', 0.0)}deg",
        f"- Typical Native Size: {props.get('native_size', [32, 32])} | Aspect: {props.get('bbox_aspect', 1.0)}",
        "",
        "## Palette Keys (use directly in spec ops)",
        f"- `ink`: `{outline.get('color', '#1c141d')}`",
    ]
    for ramp in color_model.get("ramps", []):
        rname = ramp.get("name", "ramp")
        cols = ramp.get("colors", [])
        keys = ", ".join(f"`{rname}_{i}`={hx}" for i, hx in enumerate(cols))
        lines.append(f"- **{rname}** (shift {ramp.get('hue_shift_deg', 0.0)}deg): {keys}")

    lines.append("")
    lines.append("## Agent Rules")
    for rule in profile.get("agent_rules", []):
        lines.append(f"- {rule}")

    return "\n".join(lines)


def compare_canvas_to_style(canvas: Canvas, profile: dict[str, Any]) -> dict[str, Any]:
    """Evaluate how closely a generated Canvas matches a learned `.style.json` profile."""
    opaque_colors = {c for c in canvas.pixels if c[3] > 0}
    outline_actual = analyze_outline(canvas)
    lighting_actual = analyze_lighting(canvas)
    shading_actual = analyze_shading(canvas)

    target_pal_len = max(4, len(profile.get("palette", [])))
    target_outline = profile.get("outline", {})
    target_shading = profile.get("shading", {})

    deviations: list[str] = []
    penalties = 0.0
    if not opaque_colors:
        deviations.append("Empty artwork cannot match a visual style.")
        penalties = 1.0

    # 1. Color count discipline
    if len(opaque_colors) > int(target_pal_len * 1.5) + 4:
        deviations.append(
            f"Too many colors ({len(opaque_colors)}) vs style target (~{target_pal_len})."
        )
        penalties += 0.25

    # 2. Outline mode consistency
    target_mode = target_outline.get("mode", "ext_outline")
    actual_mode = outline_actual["mode"]
    if target_mode == "lineless" and actual_mode != "lineless":
        deviations.append(f"Outline mismatch: style is 'lineless', sprite rendered as '{actual_mode}'.")
        penalties += 0.30
    elif target_mode != "lineless" and actual_mode == "lineless":
        deviations.append(f"Outline mismatch: style expects '{target_mode}', sprite is 'lineless'.")
        penalties += 0.30

    # 3. Shading/dither consistency
    target_dither = float(target_shading.get("dither_ratio", 0.0))
    actual_dither = float(shading_actual["dither_ratio"])
    if target_dither < 0.015 and actual_dither > 0.08:
        deviations.append(
            f"Over-dithered ({actual_dither:.3f}) compared to clean cel-shaded style ({target_dither:.3f})."
        )
        penalties += 0.15

    # 4. Isolated pixel noise
    if shading_actual["isolated_pixel_ratio"] > 0.12:
        deviations.append(
            f"High isolated single-pixel noise ({shading_actual['isolated_pixel_ratio']:.3f}); clean clusters."
        )
        penalties += 0.15

    score = round(max(0.0, 1.0 - penalties), 3)
    return {
        "style_name": profile.get("name", "unknown"),
        "fidelity_score": score,
        "passed": score >= 0.70,
        "deviations": deviations,
        "actual": {
            "unique_colors": len(opaque_colors),
            "outline": outline_actual,
            "lighting": lighting_actual,
            "shading": shading_actual,
        },
        "target": {
            "palette_size": target_pal_len,
            "outline_mode": target_mode,
            "lighting_direction": profile.get("lighting", {}).get("direction"),
            "shading_style": target_shading.get("style"),
        },
    }


def render_style_comparison(
    ref_path: str | Path,
    gen_path: str | Path,
    out_path: str | Path,
    *,
    profile: dict[str, Any] | None = None,
    scale: int = 6,
) -> dict[str, Any]:
    """Export a labeled side-by-side visual comparison sheet: Reference | Ingest 1:1 | Generated."""
    from PIL import Image, ImageDraw
    from pixelai.inspect_tool import load_png_as_canvas
    from pixelai.style_ingest import ingest_reference_image, slice_sprites

    ref_img = Image.open(ref_path).convert("RGBA")
    ingested = ingest_reference_image(ref_path, max_colors=24)
    sliced = slice_sprites(ingested.canvas, min_pixels=48)
    sample_canvas = sliced[0] if sliced else ingested.canvas

    gen_canvas = load_png_as_canvas(gen_path)
    fidelity = compare_canvas_to_style(gen_canvas, profile) if profile else None

    tile_sz = max(144, min(256, max(gen_canvas.width, gen_canvas.height) * max(2, scale)))

    def _canvas_to_pil(c: Canvas) -> Image.Image:
        im = Image.new("RGBA", (c.width, c.height))
        im.putdata(c.pixels)
        return im

    def _fit_tile(im: Image.Image) -> Image.Image:
        # Preserve aspect ratio with nearest-neighbor scaling inside tile_sz x tile_sz
        rw, rh = im.size
        s = min(tile_sz / max(1, rw), tile_sz / max(1, rh))
        nw = max(1, int(round(rw * s)))
        nh = max(1, int(round(rh * s)))
        resized = im.resize((nw, nh), Image.Resampling.NEAREST)
        box = Image.new("RGBA", (tile_sz, tile_sz), (26, 24, 32, 255))
        box.paste(resized, ((tile_sz - nw) // 2, (tile_sz - nh) // 2), resized)
        return box

    t_ref = _fit_tile(ref_img)
    t_ing = _fit_tile(_canvas_to_pil(sample_canvas))
    t_gen = _fit_tile(_canvas_to_pil(gen_canvas))

    score_txt = f" (score={fidelity['fidelity_score']})" if fidelity else ""
    labels = [
        f"1. Reference ({ref_img.size[0]}x{ref_img.size[1]})",
        f"2. Ingest 1:1 ({sample_canvas.width}x{sample_canvas.height})",
        f"3. Generated ({gen_canvas.width}x{gen_canvas.height}){score_txt}",
    ]

    pad = 12
    header = 28
    sheet = Image.new("RGBA", (tile_sz * 3 + pad * 4, tile_sz + header + pad), (34, 32, 42, 255))
    draw = ImageDraw.Draw(sheet)
    for idx, (tile, lbl) in enumerate(zip((t_ref, t_ing, t_gen), labels)):
        x0 = pad + idx * (tile_sz + pad)
        sheet.paste(tile, (x0, header), tile)
        draw.text((x0 + 2, 8), lbl, fill=(238, 234, 224, 255))

    dst = Path(out_path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dst)

    return {
        "comparison_image": str(dst.resolve()),
        "ingested_size": [sample_canvas.width, sample_canvas.height],
        "sliced_sprites": len(sliced),
        "fidelity": fidelity,
    }

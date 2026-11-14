"""Declarative JSON spec and multi-frame runner for pixelai-tools."""

from pathlib import Path
import json
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, TRANSPARENT, parse_color
from pixelai.exporter import extract_spec_from_png
from pixelai.inspect_tool import load_png_as_canvas
from pixelai.palettes import resolve_palette
from pixelai import autotile, filters, iso, rig


def _execute_ops(
    canvas: Canvas,
    ops: list[dict[str, Any]],
    palette: dict[str, RGBA],
    defs: dict[str, Canvas],
) -> None:
    """Execute a sequence of drawing operations on a Canvas."""
    for op in ops:
        kind = op["op"]
        if kind == "pixel":
            canvas.set_pixel(op["x"], op["y"], parse_color(op["color"], palette))
        elif kind == "line":
            canvas.draw_line(
                op["x0"], op["y0"], op["x1"], op["y1"],
                parse_color(op["color"], palette),
            )
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
        elif kind == "polygon":
            pts = [(int(p[0]), int(p[1])) for p in op["points"]]
            canvas.draw_polygon(
                pts,
                parse_color(op["color"], palette),
                filled=op.get("filled", True),
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
        elif kind == "scatter":
            tgt = (
                parse_color(op["target_color"], palette)
                if "target_color" in op
                else None
            )
            canvas.scatter(
                op.get("x", 0),
                op.get("y", 0),
                op.get("w", canvas.width),
                op.get("h", canvas.height),
                parse_color(op["color"], palette),
                density=float(op.get("density", 0.15)),
                seed=int(op.get("seed", 42)),
                target_color=tgt,
                pattern=op.get("pattern", "noise"),
            )
        elif kind == "stamp":
            def_name = op["def"]
            if def_name not in defs:
                raise ValueError(f"Unknown stamp def: {def_name!r}")
            remap = None
            if "remap" in op:
                remap = {
                    parse_color(k, palette): parse_color(v, palette)
                    for k, v in op["remap"].items()
                }
            pivot = (
                (float(op["pivot"][0]), float(op["pivot"][1]))
                if "pivot" in op
                else None
            )
            canvas.blit(
                defs[def_name],
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                flip_x=bool(op.get("flip_x", False)),
                flip_y=bool(op.get("flip_y", False)),
                remap=remap,
                angle=float(op.get("angle", 0.0)),
                pivot=pivot,
            )
        elif kind == "load_png":
            src = load_png_as_canvas(op["path"])
            if "crop" in op:
                cx, cy, cw, ch = (int(v) for v in op["crop"])
                cropped = Canvas(cw, ch)
                cropped.blit(src, -cx, -cy)
                src = cropped
            canvas.blit(
                src,
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                flip_x=bool(op.get("flip_x", False)),
                flip_y=bool(op.get("flip_y", False)),
            )
        elif kind == "tilemap":
            tw = int(op.get("tile_w", 16))
            th = int(op.get("tile_h", 16))
            ox = int(op.get("x", 0))
            oy = int(op.get("y", 0))
            mode = op.get("mode", "ortho").lower()
            mapping: dict[str, str] = op.get("map", {})
            cells: list[tuple[int, int, str]] = []
            for ry_idx, row in enumerate(op["rows"]):
                tokens = row.split() if " " in row else list(row)
                for rx_idx, tok in enumerate(tokens):
                    if tok == ".":
                        continue
                    def_key = mapping.get(tok, tok)
                    if def_key not in defs:
                        raise ValueError(f"Tilemap token {tok!r} -> {def_key!r} not in defs")
                    cells.append((rx_idx, ry_idx, def_key))
            if mode == "iso":
                step_x = int(op.get("step_x", tw // 2))
                step_y = int(op.get("step_y", th // 4))
                cells.sort(key=lambda c: c[0] + c[1])
                for rx_idx, ry_idx, def_key in cells:
                    px = ox + (rx_idx - ry_idx) * step_x
                    py = oy + (rx_idx + ry_idx) * step_y
                    canvas.blit(defs[def_key], px, py)
            else:
                for rx_idx, ry_idx, def_key in cells:
                    canvas.blit(defs[def_key], ox + rx_idx * tw, oy + ry_idx * th)
        elif kind == "autotile":
            lip = parse_color(op["lip"], palette) if "lip" in op else None
            autotile.draw_autotile_atlas(
                canvas,
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                int(op.get("tile_size", 16)),
                parse_color(op["inner"], palette),
                parse_color(op["outer"], palette),
                lip_color=lip,
                seed=int(op.get("seed", 42)),
            )
        elif kind == "char_rig":
            rig.draw_char_rig(
                canvas,
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                palette,
                op,
            )
        elif kind == "iso_tile":
            rx = int(op["rx"])
            ry = int(op.get("ry", max(1, rx // 2)))
            border = parse_color(op["border"], palette) if "border" in op else None
            iso.draw_iso_tile(
                canvas,
                int(op["cx"]),
                int(op["cy"]),
                rx,
                ry,
                parse_color(op["color"], palette),
                border=border,
            )
        elif kind == "iso_box":
            rx = int(op["rx"])
            ry = int(op.get("ry", max(1, rx // 2)))
            iso.draw_iso_box(
                canvas,
                int(op["cx"]),
                int(op["cy"]),
                rx,
                ry,
                int(op["h"]),
                parse_color(op["top"], palette),
                parse_color(op["left"], palette),
                parse_color(op["right"], palette),
                bevel=bool(op.get("bevel", True)),
                ground_shadow=int(op.get("ground_shadow", 0)),
            )
        elif kind == "iso_roof":
            rx = int(op["rx"])
            ry = int(op.get("ry", max(1, rx // 2)))
            gable = parse_color(op["gable"], palette) if "gable" in op else None
            iso.draw_iso_roof(
                canvas,
                int(op["cx"]),
                int(op["cy"]),
                rx,
                ry,
                int(op["h"]),
                parse_color(op["left"], palette),
                parse_color(op["right"], palette),
                style=op.get("style", "pyramid"),
                gable_color=gable,
                eave_shadow=bool(op.get("eave_shadow", True)),
                bevel=bool(op.get("bevel", True)),
            )
        elif kind == "iso_wall_rect":
            iso.draw_iso_wall_rect(
                canvas,
                op.get("face", "left"),
                int(op["x"]),
                int(op["y"]),
                int(op["w"]),
                int(op["h"]),
                parse_color(op["color"], palette),
                arch=bool(op.get("arch", False)),
                recessed=bool(op.get("recessed", True)),
            )
        elif kind == "iso_structure":
            iso.draw_iso_structure(
                canvas,
                int(op.get("origin_x", canvas.width // 2)),
                int(op.get("origin_y", canvas.height // 2)),
                op["items"],
                palette,
                step_x=int(op.get("step_x", 2)),
                step_y=int(op.get("step_y", 1)),
                default_bevel=bool(op.get("bevel", True)),
                default_ground_shadow=int(op.get("ground_shadow", 2)),
            )
        else:
            raise ValueError(f"Unknown op: {kind!r}")


def _resolve_post_ops(
    spec: dict[str, Any], palette: dict[str, RGBA]
) -> list[dict[str, Any]]:
    """Enforce 'ext_outline' (default when set) or 'lineless' (no external outline)."""
    style = spec.get("style")
    raw_post = list(spec.get("post", []))

    if style == "lineless":
        return [p for p in raw_post if p.get("op") != "outline"]

    if style == "ext_outline" and not any(p.get("op") == "outline" for p in raw_post):
        default_col = spec.get(
            "outline_color",
            "ink" if "ink" in palette else ("0" if "0" in palette else "#21181b"),
        )
        outline_op = {"op": "outline", "color": default_col}
        # Insert before 'scale' so the outline stays 1px in art resolution
        out: list[dict[str, Any]] = []
        inserted = False
        for p in raw_post:
            if p.get("op") == "scale" and not inserted:
                out.append(outline_op)
                inserted = True
            out.append(p)
        if not inserted:
            out.append(outline_op)
        return out

    return raw_post


def _apply_post(
    canvas: Canvas, post_ops: list[dict[str, Any]], palette: dict[str, RGBA]
) -> Canvas:
    for post in post_ops:
        kind = post["op"]
        if kind == "outline":
            canvas = filters.outline(
                canvas,
                parse_color(post["color"], palette),
                selout=bool(post.get("selout", False)),
                selout_amount=float(post.get("selout_amount", 0.55)),
                auto_pad=bool(post.get("auto_pad", False)),
            )
        elif kind == "drop_shadow":
            col = (
                parse_color(post["color"], palette)
                if "color" in post
                else (33, 24, 27, 96)
            )
            canvas = filters.drop_shadow(
                canvas,
                dx=int(post.get("dx", 1)),
                dy=int(post.get("dy", 2)),
                color=col,
            )
        elif kind == "pad":
            canvas = filters.pad(canvas, int(post.get("size", 1)))
        elif kind == "shade":
            canvas = filters.shade(canvas, float(post.get("amount", 0.25)))
        elif kind == "scale":
            canvas = filters.scale(canvas, int(post["factor"]))
        else:
            raise ValueError(f"Unknown post-processing op: {kind!r}")
    return canvas


def _resolve_extends(spec: dict[str, Any]) -> dict[str, Any]:
    """Merge parent spec from 'extends' (.png with embedded spec or .json file)."""
    if "extends" not in spec:
        return spec
    parent_path = Path(spec["extends"])
    if parent_path.suffix.lower() == ".png":
        parent = extract_spec_from_png(parent_path)
    else:
        parent = json.loads(parent_path.read_text(encoding="utf-8-sig"))

    merged = dict(parent)
    for k, v in spec.items():
        if k == "extends":
            continue
        if k in ("defs", "palette_ext") and isinstance(merged.get(k), dict) and isinstance(v, dict):
            combined = dict(merged[k])
            combined.update(v)
            merged[k] = combined
        elif k == "ops" and spec.get("inherit_ops", False):
            merged["ops"] = list(parent.get("ops", [])) + list(v)
        else:
            merged[k] = v
    return merged


def run_frames(spec: dict[str, Any]) -> tuple[list[Canvas], list[str]]:
    """Execute a spec into one or more post-processed frames and their names."""
    spec = _resolve_extends(spec)
    width = int(spec["width"])
    height = int(spec["height"])
    palette = resolve_palette(spec.get("palette"), spec.get("palette_ext"))
    bg = parse_color(spec["background"], palette) if "background" in spec else TRANSPARENT

    defs: dict[str, Canvas] = {}
    for name, dspec in spec.get("defs", {}).items():
        dw = int(dspec.get("width", width))
        dh = int(dspec.get("height", height))
        dc = Canvas(dw, dh, fill=TRANSPARENT)
        _execute_ops(dc, dspec.get("ops", []), palette, defs)
        if "post" in dspec:
            dc = _apply_post(dc, dspec["post"], palette)
        defs[name] = dc

    base_ops = spec.get("ops", [])
    post_ops = _resolve_post_ops(spec, palette)
    raw_frames = spec.get("frames")

    if not raw_frames:
        canvas = Canvas(width, height, fill=bg)
        _execute_ops(canvas, base_ops, palette, defs)
        return [_apply_post(canvas, post_ops, palette)], ["frame_0"]

    frames: list[Canvas] = []
    names: list[str] = []
    for idx, fspec in enumerate(raw_frames):
        canvas = Canvas(width, height, fill=bg)
        if fspec.get("inherit_base", True) and base_ops:
            _execute_ops(canvas, base_ops, palette, defs)
        _execute_ops(canvas, fspec.get("ops", []), palette, defs)
        frames.append(_apply_post(canvas, post_ops, palette))
        names.append(fspec.get("name", f"frame_{idx}"))
    return frames, names


def run_spec(spec: dict[str, Any]) -> Canvas:
    """Execute a declarative pixel art specification and return the first Canvas."""
    frames, _ = run_frames(spec)
    return frames[0]

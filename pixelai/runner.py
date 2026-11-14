"""Declarative JSON spec and multi-frame runner for pixelai-tools."""

from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, TRANSPARENT, parse_color
from pixelai.palettes import resolve_palette
from pixelai import filters, iso


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
            canvas.blit(
                defs[def_name],
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                flip_x=bool(op.get("flip_x", False)),
                flip_y=bool(op.get("flip_y", False)),
                remap=remap,
            )
        elif kind == "tilemap":
            tw = int(op["tile_w"])
            th = int(op["tile_h"])
            ox = int(op.get("x", 0))
            oy = int(op.get("y", 0))
            mapping: dict[str, str] = op.get("map", {})
            for ry_idx, row in enumerate(op["rows"]):
                tokens = row.split() if " " in row else list(row)
                for rx_idx, tok in enumerate(tokens):
                    if tok == ".":
                        continue
                    def_key = mapping.get(tok, tok)
                    if def_key not in defs:
                        raise ValueError(f"Tilemap token {tok!r} -> {def_key!r} not in defs")
                    canvas.blit(defs[def_key], ox + rx_idx * tw, oy + ry_idx * th)
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
            edge = parse_color(op["edge"], palette) if "edge" in op else None
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
                edge_color=edge,
            )
        elif kind == "iso_roof":
            rx = int(op["rx"])
            ry = int(op.get("ry", max(1, rx // 2)))
            gable = parse_color(op["gable"], palette) if "gable" in op else None
            ridge = parse_color(op["ridge"], palette) if "ridge" in op else None
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
                ridge_color=ridge,
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
            )
        else:
            raise ValueError(f"Unknown op: {kind!r}")


def _apply_post(
    canvas: Canvas, post_ops: list[dict[str, Any]], palette: dict[str, RGBA]
) -> Canvas:
    for post in post_ops:
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


def run_frames(spec: dict[str, Any]) -> tuple[list[Canvas], list[str]]:
    """Execute a spec into one or more post-processed frames and their names."""
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
    post_ops = spec.get("post", [])
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

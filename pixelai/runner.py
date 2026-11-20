"""Declarative JSON spec and multi-frame runner for pixelai-tools."""

from pathlib import Path
import json
from typing import Any
from pixelai.canvas import Canvas
from pixelai.color import RGBA, TRANSPARENT, parse_color
from pixelai.exporter import extract_spec_from_png
from pixelai.inspect_tool import load_png_as_canvas
from pixelai.palettes import resolve_palette
from pixelai import autotile, building, creatures, filters, iso, items, materials, nature, rig, ui


_GENERATOR_OPS = frozenset({
    "animal_rig", "char_rig", "nature_rig", "item_rig",
    "building", "portrait_rig", "ui_rig", "autotile",
    "tilemap", "iso_structure", "material",
})


def _execute_ops(
    canvas: Canvas,
    ops: list[dict[str, Any]],
    palette: dict[str, RGBA],
    defs: dict[str, Canvas],
    frame_idx: int = 0,
    total_frames: int = 1,
) -> None:
    """Execute a sequence of drawing operations on a Canvas."""
    for index, op in enumerate(ops):
        try:
            _execute_ops_unchecked(canvas, [op], palette, defs, frame_idx, total_frames)
        except KeyError as exc:
            raise ValueError(f"ops[{index}] ({op.get('op')}): missing or unknown field/key {exc}") from exc
        except (ValueError, TypeError, IndexError, OSError) as exc:
            kind = op.get("op") if isinstance(op, dict) else None
            raise ValueError(f"ops[{index}] ({kind}): {exc}") from exc


def _execute_ops_unchecked(canvas, ops, palette, defs, frame_idx, total_frames):
    for op in ops:
        kind = op["op"]
        if "z" in op:
            canvas.current_z = float(op["z"])
        else:
            canvas.current_z = None

        is_shadow_op = (
            kind not in _GENERATOR_OPS
            and (
                bool(op.get("shadow", False))
                or (kind in ("ellipse", "rect") and str(op.get("color", "")) == "shadow" and op.get("outline") is not True)
            )
        )
        canvas.mark_shadow = is_shadow_op
        if "outline" in op:
            canvas.mark_no_outline = not bool(op["outline"])
        elif kind == "particles":
            canvas.mark_no_outline = True
        else:
            canvas.mark_no_outline = is_shadow_op

        canvas.clip_to_opaque = bool(op.get("inside", op.get("clip", False)))

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
                bevel=bool(op.get("bevel", False)),
                recessed=bool(op.get("recessed", False)),
            )
        elif kind == "circle":
            canvas.draw_circle(
                op["cx"], op["cy"], op["r"],
                parse_color(op["color"], palette),
                filled=op.get("filled", False),
            )
        elif kind == "ellipse":
            canvas.draw_ellipse(
                int(op["cx"]),
                int(op["cy"]),
                int(op["rx"]),
                int(op["ry"]),
                parse_color(op["color"], palette),
                filled=bool(op.get("filled", True)),
            )
        elif kind == "bezier":
            pts = [(int(p[0]), int(p[1])) for p in op["points"]]
            canvas.draw_bezier(
                pts,
                parse_color(op["color"], palette),
                thickness=int(op.get("thickness", 1)),
            )
        elif kind == "particles":
            pw = int(op.get("w", canvas.width))
            ph = int(op.get("h", canvas.height))
            mode = op.get("mode", "smoke")
            px = int(op.get("x", 0))
            py = int(op.get("y", 0))
            if mode == "smoke" and canvas.last_chimney is not None and op.get("attach_chimney", True):
                ccx, ccy = canvas.last_chimney
                if "x" not in op or abs((px + pw // 2) - ccx) > 3 or (py + ph) > ccy + 2:
                    px = ccx - pw // 2
                    py = max(0, ccy - ph)
            canvas.draw_particles(
                px,
                py,
                pw,
                ph,
                int(op.get("count", 8)),
                parse_color(op["color"], palette),
                frame=int(op.get("frame", frame_idx)),
                total_frames=int(op.get("total_frames", max(1, total_frames))),
                mode=mode,
                size=int(op.get("size", 1)),
                seed=int(op.get("seed", 42)),
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
        elif kind == "portrait_rig":
            rig.draw_portrait_rig(
                canvas,
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                palette,
                op,
            )
        elif kind == "animal_rig":
            creatures.draw_animal_rig(
                canvas,
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                palette,
                op,
                frame_idx=frame_idx,
                total_frames=total_frames,
            )
        elif kind == "emote":
            creatures.draw_emote(
                canvas,
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                op.get("kind", "heart"),
                frame=int(op.get("frame", frame_idx)),
                palette=palette,
                outline=bool(op.get("outline", False)),
            )
        elif kind == "building":
            building.draw_building(
                canvas,
                palette,
                op,
                frame_idx=frame_idx,
                total_frames=total_frames,
            )
        elif kind == "item_rig":
            items.draw_item_rig(
                canvas,
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                palette,
                op,
                frame_idx=frame_idx,
                total_frames=total_frames,
            )
        elif kind == "nature_rig":
            nature.draw_nature_rig(
                canvas,
                int(op.get("x", 0)),
                int(op.get("y", 0)),
                palette,
                op,
                frame_idx=frame_idx,
                total_frames=total_frames,
            )
        elif kind == "material":
            materials.draw_material(canvas, int(op.get("x", 0)), int(op.get("y", 0)), palette, op)
        elif kind == "ui_rig":
            ui.draw_ui_rig(
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
            wins = op.get("windows") or ([op["window"]] if "window" in op else None)
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
                door=op.get("door"),
                windows=wins,
                roof=op.get("roof"),
                palette=palette,
            )
        elif kind == "iso_roof":
            rx = int(op["rx"]) if "rx" in op else None
            ry = int(op["ry"]) if "ry" in op else (max(1, rx // 2) if rx is not None else None)
            gable = parse_color(op["gable"], palette) if "gable" in op else None
            iso.draw_iso_roof(
                canvas,
                int(op["cx"]) if "cx" in op else None,
                int(op["cy"]) if "cy" in op else None,
                rx,
                ry,
                int(op.get("h", 8)),
                parse_color(op.get("left", "roof_l"), palette),
                parse_color(op.get("right", "roof_d"), palette),
                style=op.get("style", "pyramid"),
                gable_color=gable,
                eave_shadow=bool(op.get("eave_shadow", True)),
                bevel=bool(op.get("bevel", True)),
                chimney=op.get("chimney", False),
                palette=palette,
            )
        elif kind == "iso_wall_rect":
            iso.draw_iso_wall_rect(
                canvas,
                op.get("face", "left"),
                int(op["x"]) if "x" in op else None,
                int(op["y"]) if "y" in op else None,
                int(op.get("w", 4)),
                int(op.get("h", 6)),
                parse_color(op.get("color", "wood_d"), palette),
                arch=bool(op.get("arch", False)),
                recessed=bool(op.get("recessed", True)),
                role=op.get("role"),
            )
        elif kind == "iso_structure":
            iso.draw_iso_structure(
                canvas,
                int(op.get("origin_x", canvas.width // 2)),
                int(op.get("origin_y", canvas.height // 2)),
                op["items"],
                palette,
                step_x=int(op["step_x"]) if "step_x" in op else None,
                step_y=int(op["step_y"]) if "step_y" in op else None,
                default_bevel=bool(op.get("bevel", True)),
                default_ground_shadow=int(op.get("ground_shadow", 2)),
            )
        else:
            raise ValueError(f"Unknown op: {kind!r}")
        canvas.mark_no_outline = False
        canvas.mark_shadow = False
        canvas.clip_to_opaque = False


def _resolve_post_ops(
    spec: dict[str, Any], palette: dict[str, RGBA]
) -> list[dict[str, Any]]:
    """Enforce 'ext_outline' (default when set) or 'lineless' (no external outline)."""
    style = spec.get("style")
    raw_post = list(spec.get("post", []))

    if style == "lineless":
        return [p for p in raw_post if p.get("op") != "outline"]

    if style == "ext_outline" and not any(p.get("op") == "outline" for p in raw_post):
        fallback_col: Any = "#21181b"
        if "ink" in palette:
            fallback_col = "ink"
        elif "0" in palette:
            c0 = palette["0"]
            lum = c0[0] * 0.299 + c0[1] * 0.587 + c0[2] * 0.114
            if lum < 65:
                fallback_col = "0"
        default_col = spec.get("outline_color", fallback_col)
        outline_op: dict[str, Any] = {"op": "outline", "color": default_col}
        if spec.get("auto_pad"):
            outline_op["auto_pad"] = True
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
            canvas = filters.shade(
                canvas,
                float(post.get("amount", 0.25)),
                hue_shift=bool(post.get("hue_shift", False)),
            )
        elif kind == "scale":
            canvas = filters.scale(canvas, int(post["factor"]))
        else:
            raise ValueError(f"Unknown post-processing op: {kind!r}")
    return canvas


def resolve_spec_paths(spec: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Anchor declared input paths to the directory containing the spec."""
    if not isinstance(spec, dict):
        raise ValueError("spec: expected a JSON object")
    spec = dict(spec)
    if "extends" in spec:
        spec["extends"] = str((base_dir / spec["extends"]).resolve())
    for key in ("ops", "layers", "frames", "keyframes"):
        if key not in spec:
            continue
        if not isinstance(spec[key], list):
            raise ValueError(f"{key}: expected an array")
        entries = []
        for index, entry in enumerate(spec[key]):
            if not isinstance(entry, dict):
                raise ValueError(f"{key}[{index}]: expected an object")
            if key != "ops":
                entry = resolve_spec_paths(entry, base_dir)
            elif entry.get("op") == "load_png" and "path" in entry:
                if not isinstance(entry["path"], str):
                    raise ValueError(f"ops[{index}] (load_png): path must be a string")
                entry = {**entry, "path": str((base_dir / entry["path"]).resolve())}
            entries.append(entry)
        spec[key] = entries
    if "defs" in spec:
        if not isinstance(spec["defs"], dict):
            raise ValueError("defs: expected an object")
        spec["defs"] = {
            name: resolve_spec_paths(definition, base_dir)
            for name, definition in spec["defs"].items()
        }
    return spec


def _check_fresh(spec: dict[str, Any]) -> None:
    """Reject external asset reuse throughout a fresh generation spec."""
    if "fresh" in spec and not isinstance(spec["fresh"], bool):
        raise ValueError("fresh must be a boolean")
    def visit(value, path):
        if isinstance(value, dict):
            if "extends" in value or value.get("op") == "load_png":
                raise ValueError(f"{path}: fresh generation forbids extends and load_png; draw a new asset")
            for key, child in value.items():
                visit(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")
    if spec.get("fresh", False):
        visit(spec, "spec")


def _resolve_extends(spec: dict[str, Any]) -> dict[str, Any]:
    """Merge parent spec from 'extends' (.png with embedded spec or .json file)."""
    _check_fresh(spec)
    if "extends" not in spec:
        return spec
    parent_path = Path(spec["extends"])
    if parent_path.suffix.lower() == ".png":
        parent = extract_spec_from_png(parent_path)
    else:
        parent = json.loads(parent_path.read_text(encoding="utf-8-sig"))

    merged = resolve_spec_paths(parent, parent_path.resolve().parent)
    for k, v in spec.items():
        if k == "extends":
            continue
        if k in ("defs", "palette_ext") and isinstance(merged.get(k), dict) and isinstance(v, dict):
            combined = dict(merged[k])
            combined.update(v)
            merged[k] = combined
        elif k == "ops" and spec.get("inherit_ops", False):
            merged["ops"] = list(merged.get("ops", [])) + list(v)
        else:
            merged[k] = v
    _check_fresh(merged)
    return merged


_TWEEN_KEYS = ("x", "y", "cx", "cy", "rx", "ry", "r", "w", "h", "angle", "x0", "y0", "x1", "y1")


def _expand_keyframes(keyframes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interpolate numeric op properties across consecutive keyframes."""
    if not keyframes:
        return []
    expanded: list[dict[str, Any]] = []
    for k_idx, kf in enumerate(keyframes):
        steps = max(1, int(kf.get("steps", 1)))
        base_name = kf.get("name", f"kf_{k_idx}")
        ops_a = kf.get("ops", [])
        if k_idx + 1 >= len(keyframes) or steps == 1:
            expanded.append({"name": base_name, "ops": ops_a, "inherit_base": kf.get("inherit_base", True)})
            continue
        ops_b = keyframes[k_idx + 1].get("ops", [])
        for s in range(steps):
            t = s / steps
            interp_ops: list[dict[str, Any]] = []
            for idx, op_a in enumerate(ops_a):
                if idx < len(ops_b) and ops_b[idx].get("op") == op_a.get("op"):
                    op_b = ops_b[idx]
                    new_op = dict(op_a)
                    for tk in _TWEEN_KEYS:
                        if tk in op_a and tk in op_b:
                            val = float(op_a[tk]) * (1.0 - t) + float(op_b[tk]) * t
                            new_op[tk] = val if tk == "angle" else int(round(val))
                    interp_ops.append(new_op)
                else:
                    interp_ops.append(dict(op_a))
            expanded.append({
                "name": f"{base_name}_{s}",
                "ops": interp_ops,
                "inherit_base": kf.get("inherit_base", True),
            })
    return expanded


def run_layers(spec: dict[str, Any]) -> list[tuple[str, Canvas]]:
    """Render each named layer in `spec['layers']` into its own separate Canvas."""
    spec = _resolve_extends(spec)
    width = int(spec["width"])
    height = int(spec["height"])
    palette = resolve_palette(spec.get("palette"), spec.get("palette_ext"))

    defs: dict[str, Canvas] = {}
    for name, dspec in spec.get("defs", {}).items():
        dw = int(dspec.get("width", width))
        dh = int(dspec.get("height", height))
        dc = Canvas(dw, dh, fill=TRANSPARENT)
        _execute_ops(dc, dspec.get("ops", []), palette, defs)
        if "post" in dspec:
            dc = _apply_post(dc, dspec["post"], palette)
        defs[name] = dc

    result: list[tuple[str, Canvas]] = []
    for idx, lspec in enumerate(spec.get("layers", [])):
        lname = lspec.get("name", f"layer_{idx}")
        lc = Canvas(width, height, fill=TRANSPARENT)
        _execute_ops(lc, lspec.get("ops", []), palette, defs)
        if "post" in lspec:
            lc = _apply_post(lc, lspec["post"], palette)
        result.append((lname, lc))
    return result


def _merge_frame_ops_into_base(
    base_ops: list[dict[str, Any]], frame_ops: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Merge frame/keyframe ops into base_ops without burying foreground structures under shadows."""
    if not base_ops:
        return list(frame_ops)
    if not frame_ops:
        return list(base_ops)
    merged = [dict(op) for op in base_ops]
    appended: list[dict[str, Any]] = []
    for fop in frame_ops:
        # If frame op matches a background/shadow op already in base_ops, update it in-place
        replaced = False
        for idx, bop in enumerate(merged):
            if (
                bop.get("op") == fop.get("op")
                and bop.get("color") == fop.get("color")
                and fop.get("op") in ("ellipse", "particles")
            ):
                merged[idx] = dict(fop)
                replaced = True
                break
        if not replaced:
            if fop.get("op") == "ellipse" and str(fop.get("color", "")).startswith("shadow"):
                merged.insert(0, dict(fop))
            else:
                appended.append(dict(fop))
    return merged + appended


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

    base_ops = list(spec.get("ops", []))
    for lspec in spec.get("layers", []):
        base_ops.extend(lspec.get("ops", []))

    post_ops = _resolve_post_ops(spec, palette)
    raw_frames = spec.get("frames")
    if not raw_frames and "keyframes" in spec:
        raw_frames = _expand_keyframes(spec["keyframes"])
    if not raw_frames and (
        "frame_count" in spec
        or any(op.get("op") in ("particles", "animal_rig", "emote") for op in base_ops)
        or any(op.get("op") == "nature_rig" and op.get("sway") for op in base_ops)
    ):
        default_fc = 6 if any(op.get("pose") == "peck" for op in base_ops) else (
            4 if (
                any(op.get("op") in ("particles", "animal_rig", "emote") for op in base_ops)
                or any(op.get("op") == "nature_rig" and op.get("sway") for op in base_ops)
            ) else 1
        )
        fc = int(spec.get("frame_count", default_fc))
        if fc > 1:
            raw_frames = [{"name": f"frame_{i}", "ops": []} for i in range(fc)]

    if not raw_frames:
        canvas = Canvas(width, height, fill=bg)
        _execute_ops(canvas, _merge_frame_ops_into_base([], base_ops), palette, defs, frame_idx=0, total_frames=1)
        return [_apply_post(canvas, post_ops, palette)], ["frame_0"]

    total = len(raw_frames)
    frames: list[Canvas] = []
    names: list[str] = []
    for idx, fspec in enumerate(raw_frames):
        canvas = Canvas(width, height, fill=bg)
        effective_ops = (
            _merge_frame_ops_into_base(base_ops, fspec.get("ops", []))
            if fspec.get("inherit_base", True)
            else list(fspec.get("ops", []))
        )
        _execute_ops(canvas, effective_ops, palette, defs, frame_idx=idx, total_frames=total)
        frames.append(_apply_post(canvas, post_ops, palette))
        names.append(fspec.get("name", f"frame_{idx}"))
    return frames, names


def run_spec(spec: dict[str, Any]) -> Canvas:
    """Execute a declarative pixel art specification and return the first Canvas."""
    frames, _ = run_frames(spec)
    return frames[0]

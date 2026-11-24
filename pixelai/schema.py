"""JSON Schema, modular per-op documentation, and fuzzy field linting for AI agents."""

from __future__ import annotations

import difflib
from typing import Any

from pixelai.palettes import list_palettes

UNIVERSAL_OP_FIELDS: frozenset[str] = frozenset({"op", "z", "inside", "clip", "outline", "shadow"})

OP_SPECS: dict[str, dict[str, Any]] = {
    "pixel": {
        "summary": "Set a single pixel at (x, y).",
        "required": ["x", "y", "color"],
        "optional": [],
        "example": {"op": "pixel", "x": 4, "y": 4, "color": "ink"},
    },
    "line": {
        "summary": "Draw a 1px Bresenham line from (x0, y0) to (x1, y1).",
        "required": ["x0", "y0", "x1", "y1", "color"],
        "optional": [],
        "example": {"op": "line", "x0": 2, "y0": 2, "x1": 14, "y1": 10, "color": "wood"},
    },
    "rect": {
        "summary": "Draw a filled or outlined rectangle with optional bevel or recessed lip.",
        "required": ["x", "y", "w", "h", "color"],
        "optional": ["filled", "bevel", "recessed"],
        "example": {"op": "rect", "x": 4, "y": 4, "w": 16, "h": 12, "color": "wood", "bevel": True},
    },
    "circle": {
        "summary": "Draw a midpoint pixel-art circle centered at (cx, cy) with radius r.",
        "required": ["cx", "cy", "r", "color"],
        "optional": ["filled"],
        "example": {"op": "circle", "cx": 16, "cy": 16, "r": 8, "color": "grass", "filled": True},
    },
    "ellipse": {
        "summary": "Draw a filled or outlined ellipse centered at (cx, cy) with radii (rx, ry).",
        "required": ["cx", "cy", "rx", "ry", "color"],
        "optional": ["filled"],
        "example": {"op": "ellipse", "cx": 16, "cy": 24, "rx": 10, "ry": 4, "color": "shadow"},
    },
    "bezier": {
        "summary": "Draw a quadratic or N-degree Bezier curve through control points.",
        "required": ["points", "color"],
        "optional": ["thickness"],
        "example": {"op": "bezier", "points": [[2, 20], [16, 4], [30, 20]], "color": "wood", "thickness": 2},
    },
    "polygon": {
        "summary": "Draw a filled or outlined polygon from [x, y] vertices.",
        "required": ["points", "color"],
        "optional": ["filled"],
        "example": {"op": "polygon", "points": [[4, 16], [16, 4], [28, 16]], "color": "roof", "filled": True},
    },
    "fill": {
        "summary": "4-way flood fill starting at (x, y).",
        "required": ["x", "y", "color"],
        "optional": [],
        "example": {"op": "fill", "x": 8, "y": 8, "color": "water"},
    },
    "grid": {
        "summary": "Draw pixels from an ASCII art row grid ('.' and ' ' are transparent).",
        "required": ["rows"],
        "optional": ["x", "y", "colors"],
        "example": {"op": "grid", "x": 0, "y": 0, "rows": ["..oo..", ".oggo."]},
    },
    "dither": {
        "summary": "Fill a rectangle with checkerboard or Bayer 4x4 ordered dithering.",
        "required": ["x", "y", "w", "h", "color_a", "color_b"],
        "optional": ["mode", "ratio"],
        "example": {"op": "dither", "x": 0, "y": 0, "w": 16, "h": 16, "color_a": "grass", "color_b": "grass_d", "mode": "bayer4", "ratio": 0.5},
    },
    "band_gradient": {
        "summary": "Flat color bands with Bayer 4x4 dithering strictly along band edges.",
        "required": [],
        "optional": ["x", "y", "w", "h", "ramp", "hue_ramp", "color", "direction", "strip"],
        "example": {"op": "band_gradient", "x": 0, "y": 0, "w": 32, "h": 16, "hue_ramp": {"n": 5, "hue": 210}, "direction": "vertical", "strip": 0.33},
    },
    "solid": {
        "summary": "Smooth-min SDF metaball union of capsules/ellipsoids with normal-mapped lighting.",
        "required": ["primitives"],
        "optional": ["ramp", "hue_ramp", "color", "light", "k", "ambient", "dark", "gloss", "shine", "cut", "inflate", "inflate_mix", "dither_strip"],
        "example": {"op": "solid", "primitives": [{"type": "capsule", "ax": 16, "ay": 10, "bx": 16, "by": 24, "ra": 5, "rb": 7}], "hue_ramp": {"n": 5, "hue": 140}, "inflate": 3},
    },
    "flame": {
        "summary": "Deterministic FBM-driven animated pixel-art flame with rising embers.",
        "required": [],
        "optional": ["x", "y", "ground", "t", "height", "width", "ramp", "speed", "rough", "sway_amp", "dither_strip", "seed", "embers"],
        "example": {"op": "flame", "x": 16, "ground": 30, "height": 22, "width": 7, "embers": 4},
    },
    "smoke": {
        "summary": "Deterministic FBM-warped translucent pixel-art smoke plume.",
        "required": [],
        "optional": ["x", "y", "ground", "t", "height", "width", "ramp", "speed", "rough", "sway_amp", "warp", "dither_strip", "seed"],
        "example": {"op": "smoke", "x": 16, "ground": 28, "height": 32, "width": 2.5, "warp": 18},
    },
    "ik_limb": {
        "summary": "2-bone analytical inverse kinematics limb rendered with smooth SDF shading.",
        "required": ["start", "target", "l1", "l2"],
        "optional": ["color", "direction", "dir", "radius", "radius_a", "radius_b", "radius_c", "ramp"],
        "example": {"op": "ik_limb", "start": [10, 16], "target": [22, 26], "l1": 9, "l2": 9, "direction": 1, "color": "wood"},
    },
    "bend": {
        "summary": "Inverse-bilinear spine deformation of a named `def` via `pose` or auto-animated `wave`.",
        "required": ["def", "rest"],
        "optional": ["pose", "wave", "reach", "x", "y"],
        "example": {"op": "bend", "def": "tail", "rest": [[4, 16], [16, 16], [28, 16]], "wave": {"amp": 3.0, "wavelength": 16.0, "from": 0.1}},
    },
    "spine_rig": {
        "summary": "Full-body Spine + 2-bone IK animated biped creature with guaranteed forward gait, anatomical knee/elbow bends, depth-darkened far limbs, and strict back-to-front Z-order.",
        "required": [],
        "optional": ["cx", "ground_y", "facing", "dir", "action", "pose", "frame", "total_frames", "body_hue", "hue", "body_sat", "sat", "eye_color", "horns", "tail", "scale", "shadow"],
        "example": {"op": "spine_rig", "facing": "right", "action": "walk", "body_hue": 270, "horns": True, "tail": True},
    },
    "text": {
        "summary": "Render crisp 3x5 bitmap pixel text.",
        "required": ["text"],
        "optional": ["x", "y", "color", "scale"],
        "example": {"op": "text", "x": 2, "y": 2, "text": "LV 9", "color": "#ffffff", "scale": 1},
    },
    "particles": {
        "summary": "Looping procedural particles (smoke, leaves, rain, sparks).",
        "required": ["color"],
        "optional": ["x", "y", "w", "h", "count", "frame", "total_frames", "mode", "size", "seed", "attach_chimney"],
        "example": {"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 10, "color": "cream", "mode": "sparks"},
    },
    "scatter": {
        "summary": "Procedural surface texture accents clipped to target_color.",
        "required": ["color"],
        "optional": ["x", "y", "w", "h", "density", "seed", "target_color", "pattern"],
        "example": {"op": "scatter", "x": 0, "y": 0, "w": 32, "h": 32, "color": "grass_l", "target_color": "grass", "pattern": "grass"},
    },
    "stamp": {
        "summary": "Blit a reusable `def` canvas with optional flip, rotation, ramp_shift, and color remap.",
        "required": ["def"],
        "optional": ["x", "y", "flip_x", "flip_y", "remap", "angle", "pivot", "ramp_shift"],
        "example": {"op": "stamp", "def": "leaf", "x": 8, "y": 8, "angle": 45},
    },
    "load_png": {
        "summary": "Blit an external PNG file (forbidden in `--fresh` mode).",
        "required": ["path"],
        "optional": ["x", "y", "crop", "flip_x", "flip_y"],
        "example": {"op": "load_png", "path": "base.png", "x": 0, "y": 0},
    },
    "mirror_x": {"summary": "Mirror left half of canvas onto right half.", "required": [], "optional": [], "example": {"op": "mirror_x"}},
    "mirror_y": {"summary": "Mirror top half of canvas onto bottom half.", "required": [], "optional": [], "example": {"op": "mirror_y"}},
    "material": {"summary": "Structured native material plane (rock, cobble, soil, leaves, bark, grass, water, cloth, wood, roof).", "required": ["kind"], "optional": ["x", "y", "w", "h", "seed", "color", "colors"], "flexible": True, "example": {"op": "material", "kind": "rock", "x": 0, "y": 0, "w": 32, "h": 32}},
    "building": {"summary": "Top-down 3/4 cozy building generator.", "required": [], "optional": ["x", "y", "w", "h", "roof_style", "wall_color", "roof_color", "timber_frame", "chimney", "smoke", "shadow_opacity"], "flexible": True, "example": {"op": "building", "x": 8, "y": 10, "w": 64, "h": 64}},
    "tilemap": {"summary": "Ortho or 2:1 isometric tilemap composer.", "required": ["map", "rows"], "optional": ["mode", "tile_w", "tile_h", "x", "y"], "flexible": True, "example": {"op": "tilemap", "mode": "ortho", "tile_w": 16, "tile_h": 16, "map": {"G": "grass"}, "rows": ["GG", "GG"]}},
    "autotile": {"summary": "16-tile Wang bitmask autotile atlas.", "required": [], "optional": ["x", "y", "tile_size", "inner", "outer", "lip", "seed"], "flexible": True, "example": {"op": "autotile", "tile_size": 16, "inner": "water", "outer": "grass"}},
    "char_rig": {"summary": "4/8-direction humanoid character rig (16/32/64/128px).", "required": [], "optional": ["x", "y", "size", "dir", "pose", "perspective", "frame", "hat", "shirt", "pants"], "flexible": True, "example": {"op": "char_rig", "size": 32, "dir": "down", "pose": "idle"}},
    "portrait_rig": {"summary": "Bust / Fields-of-Mistria style character portrait generator.", "required": [], "optional": ["x", "y", "width", "height", "style", "preset", "face_dir"], "flexible": True, "example": {"op": "portrait_rig", "width": 64, "height": 80, "face_dir": "front"}},
    "animal_rig": {"summary": "Cozy farm animal rig (chicken, cow, pig, sheep, duck, rabbit).", "required": [], "optional": ["x", "y", "species", "variant", "dir", "pose", "perspective", "frame", "emotes"], "flexible": True, "example": {"op": "animal_rig", "species": "chicken", "dir": "right", "pose": "walk"}},
    "item_rig": {"summary": "Parametric RPG item generator (potion, sword, shield, gem, lantern, etc.).", "required": [], "optional": ["x", "y", "kind", "size", "orientation", "state", "shine"], "flexible": True, "example": {"op": "item_rig", "kind": "potion", "size": 24}},
    "nature_rig": {"summary": "Trees, bushes, rocks, flowers, and 4-stage crops.", "required": [], "optional": ["x", "y", "kind", "variant", "stage", "sway", "ground_base"], "flexible": True, "example": {"op": "nature_rig", "kind": "tree", "variant": "oak"}},
    "ui_rig": {"summary": "Native-dimension pixel UI (panel, bar, button, heart, slot).", "required": [], "optional": ["x", "y", "kind", "theme", "state", "fill", "w", "h"], "flexible": True, "example": {"op": "ui_rig", "kind": "panel", "theme": "wood", "w": 64, "h": 32}},
    "emote": {"summary": "Floating pixel emote bubble (heart, angry, sweat, zzz, exclamation, sick).", "required": [], "optional": ["x", "y", "kind", "frame"], "flexible": True, "example": {"op": "emote", "x": 16, "y": 2, "kind": "heart"}},
    "iso_tile": {"summary": "2:1 isometric diamond ground tile.", "required": ["cx", "cy", "rx", "ry", "color"], "optional": [], "flexible": True, "example": {"op": "iso_tile", "cx": 32, "cy": 32, "rx": 16, "ry": 8, "color": "grass"}},
    "iso_box": {"summary": "2:1 isometric extruded box with bevel and ground shadow.", "required": ["cx", "cy", "rx", "ry", "h"], "optional": ["top", "left", "right", "bevel", "ground_shadow"], "flexible": True, "example": {"op": "iso_box", "cx": 32, "cy": 32, "rx": 12, "ry": 6, "h": 10}},
    "iso_roof": {"summary": "2:1 isometric pyramid or gabled roof.", "required": ["cx", "cy", "rx", "ry", "h"], "optional": ["style", "left", "right", "gable", "eave_shadow", "bevel"], "flexible": True, "example": {"op": "iso_roof", "cx": 32, "cy": 32, "rx": 12, "ry": 6, "h": 8, "style": "pyramid"}},
    "iso_wall_rect": {"summary": "2:1 isometric wall opening (door/window) on left or right face.", "required": ["face", "x", "y"], "optional": ["w", "h", "color", "arch", "recessed", "role"], "flexible": True, "example": {"op": "iso_wall_rect", "face": "left", "x": 24, "y": 36, "w": 4, "h": 6}},
    "iso_structure": {"summary": "Depth-sorted multi-part 2:1 isometric structure with per-pixel Z-buffer.", "required": ["items"], "optional": ["origin_x", "origin_y", "step_x", "step_y", "bevel", "ground_shadow"], "flexible": True, "example": {"op": "iso_structure", "origin_x": 32, "origin_y": 30, "items": []}},
}

POST_OP_SPECS: dict[str, dict[str, Any]] = {
    "outline": {"required": ["color"], "optional": ["selout", "selout_amount", "auto_pad", "directional_selout", "clean_jaggies"]},
    "recolor_material": {"required": ["material"], "optional": ["target_colors", "reflectance", "recolor_outline"]},
    "drop_shadow": {"required": [], "optional": ["dx", "dy", "color"]},
    "pad": {"required": [], "optional": ["size"]},
    "shade": {"required": [], "optional": ["amount", "hue_shift"]},
    "cleanup": {"required": [], "optional": ["tol", "keep_lone"]},
    "pixel_perfect": {"required": [], "optional": []},
    "rim_light": {"required": [], "optional": ["ramp", "dir", "direction", "steps"]},
    "scale": {"required": ["factor"], "optional": []},
}


def lint_op_fields(op: dict[str, Any]) -> list[str]:
    """Return actionable warnings for unknown/misspelled fields on a drawing op."""
    kind = op.get("op")
    spec = OP_SPECS.get(str(kind))
    if not spec or spec.get("flexible"):
        return []
    allowed = UNIVERSAL_OP_FIELDS | set(spec["required"]) | set(spec["optional"])
    warnings: list[str] = []
    for key in op:
        if key not in allowed:
            match = difflib.get_close_matches(key, sorted(allowed), n=1, cutoff=0.55)
            hint = f"; did you mean {match[0]!r}?" if match else ""
            warnings.append(f"Unknown field {key!r} in op {kind!r}{hint}")
    return warnings


def lint_post_fields(post: dict[str, Any]) -> list[str]:
    """Return actionable warnings for unknown/misspelled fields on a post-processing op."""
    kind = post.get("op")
    spec = POST_OP_SPECS.get(str(kind))
    if not spec:
        return []
    allowed = {"op"} | set(spec["required"]) | set(spec["optional"])
    warnings: list[str] = []
    for key in post:
        if key not in allowed:
            match = difflib.get_close_matches(key, sorted(allowed), n=1, cutoff=0.55)
            hint = f"; did you mean {match[0]!r}?" if match else ""
            warnings.append(f"Unknown field {key!r} in post op {kind!r}{hint}")
    return warnings


def format_op_list() -> str:
    """Return a compact, token-efficient list of all ops, post ops, and palettes."""
    lines = ["# pixelai-tools — Ops & Post-Processing Index", "", "## Drawing Ops (`ops`)"]
    for name, meta in OP_SPECS.items():
        lines.append(f"- `{name}`: {meta['summary']}")
    lines.append("")
    lines.append("## Post-Processing Ops (`post`)")
    lines.append("- " + ", ".join(f"`{k}`" for k in POST_OP_SPECS))
    lines.append("")
    lines.append("## Palettes")
    lines.append("- " + ", ".join(f"`{k}`" for k in list_palettes()))
    lines.append("")
    lines.append("Run `pixelai guide --op <name>` for detailed fields and an example.")
    return "\n".join(lines)


def format_op_guide(op_name: str) -> str:
    """Return focused documentation for a single drawing op or post-processing op."""
    import json

    key = op_name.strip().lower()
    if key in OP_SPECS:
        meta = OP_SPECS[key]
        lines = [
            f"# op: `{key}`",
            meta["summary"],
            f"- Required fields: {', '.join(meta['required']) or 'none'}",
            f"- Optional fields: {', '.join(meta['optional']) or 'none'}",
            f"- Universal flags: {', '.join(sorted(UNIVERSAL_OP_FIELDS - {'op'}))}",
            "",
            "Example:",
            json.dumps(meta["example"], indent=2),
        ]
        return "\n".join(lines)
    if key in POST_OP_SPECS:
        meta = POST_OP_SPECS[key]
        return "\n".join([
            f"# post op: `{key}`",
            f"- Required fields: {', '.join(meta['required']) or 'none'}",
            f"- Optional fields: {', '.join(meta['optional']) or 'none'}",
        ])
    all_names = sorted(set(OP_SPECS) | set(POST_OP_SPECS))
    match = difflib.get_close_matches(key, all_names, n=3, cutoff=0.5)
    hint = f" Did you mean: {', '.join(match)}?" if match else ""
    raise ValueError(f"Unknown op {op_name!r}.{hint}")


def build_json_schema() -> dict[str, Any]:
    """Build a JSON Schema (draft-07) for PixelAI-Tools declarative JSON specs."""
    op_names = sorted(OP_SPECS)
    post_names = sorted(POST_OP_SPECS)
    palette_names = sorted(list_palettes())
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "PixelAI-Tools Spec",
        "type": "object",
        "required": ["width", "height"],
        "properties": {
            "width": {"type": "integer", "minimum": 1},
            "height": {"type": "integer", "minimum": 1},
            "palette": {"oneOf": [{"type": "string", "enum": palette_names}, {"type": "object"}]},
            "palette_ext": {"type": "object", "additionalProperties": {"type": "string"}},
            "style": {"type": "string", "enum": ["ext_outline", "lineless"]},
            "style_profile": {"type": "string", "enum": ["cozy_modern", "16bit_cluster", "crisp_retro", "enchanted_hd"]},
            "outline_color": {"type": "string"},
            "auto_pad": {"type": "boolean"},
            "fresh": {"type": "boolean"},
            "material": {"type": "string"},
            "fps": {"type": "integer", "minimum": 1},
            "frame_count": {"type": "integer", "minimum": 1},
            "extends": {"type": "string"},
            "imports": {"type": "array", "items": {"type": "string"}},
            "defs": {"type": "object"},
            "ops": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["op"],
                    "properties": {"op": {"type": "string", "enum": op_names}},
                },
            },
            "post": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["op"],
                    "properties": {"op": {"type": "string", "enum": post_names}},
                },
            },
            "fx": {"type": "array", "items": {"type": "object"}},
            "frames": {"type": "array", "items": {"type": "object"}},
            "keyframes": {"type": "array", "items": {"type": "object"}},
            "layers": {"type": "array", "items": {"type": "object"}},
        },
    }

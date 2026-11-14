"""CLI entry point for pixelai-tools."""

import argparse
import json
import sys
from pathlib import Path

from pixelai import __version__
from pixelai.exporter import (
    export_gif,
    export_godot_tres,
    export_layers,
    export_png,
    export_spritesheet,
    extract_spec_from_png,
)
from pixelai.inspect_tool import analyze_canvas, load_png_as_canvas, render_ascii
from pixelai.palettes import list_palettes
from pixelai.runner import run_frames, run_layers

AGENT_GUIDE = """# pixelai-tools — Agent Reference Guide

## Aesthetic Standard (Mandatory)
- **Default (`"style": "ext_outline"`):** **Lineless Interior + 1px External Outline**. Internal surfaces use pure color planes, specular bevels (`bevel: true`), eave/ground shadows, and recessed openings (`recessed: true`) with ZERO dark internal lines, wrapped in a 1px external silhouette outline.
- **Pure Lineless (`"style": "lineless"` or `--lineless`):** **100% Lineless** (no internal or external outlines).
- **Discarded:** Dark internal outlines (`edge`/`ridge`) are permanently disabled.

## CLI Usage
- Default (Lineless Interior + External Outline): `pixelai render spec.json -o out.png`
- Pure Lineless (0 outlines): `pixelai render spec.json -o out.png --lineless`
- Animated GIF: `pixelai render spec.json -o anim.gif --fps 8`
- Spritesheet + Metadata + Godot 4 `.tres`:
  `pixelai render spec.json -o sheet.png --sheet --columns 4 --meta sheet.json --godot sheet.tres`
- Terminal Inspection (Metrics + ASCII): `pixelai inspect out.png --ascii`
- Extract Embedded Spec from PNG: `pixelai extract out.png`

## Drawing Operations (`ops`)
- `{"op": "pixel", "x": 0, "y": 0, "color": "ink"}`
- `{"op": "line", "x0": 0, "y0": 0, "x1": 5, "y1": 5, "color": "ink"}`
- `{"op": "rect", "x": 0, "y": 0, "w": 8, "h": 8, "color": "wood", "filled": true}`
- `{"op": "circle", "cx": 8, "cy": 8, "r": 4, "color": "grass", "filled": true}`
- `{"op": "ellipse", "cx": 16, "cy": 28, "rx": 8, "ry": 3, "color": "shadow", "filled": true}`
- `{"op": "bezier", "points": [[2, 20], [16, 4], [30, 20]], "color": "wood", "thickness": 2}`
- `{"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 10, "color": "cream", "mode": "smoke|leaves|rain|sparks", "size": 1, "seed": 42}`
- `{"op": "polygon", "points": [[0,0], [8,4], [0,8]], "color": "roof", "filled": true}`
- `{"op": "fill", "x": 4, "y": 4, "color": "water"}`
- `{"op": "grid", "x": 0, "y": 0, "rows": ["..oo..", ".oggo."]}` (`.` and ` ` = transparent)
- `{"op": "dither", "x": 0, "y": 0, "w": 8, "h": 8, "color_a": "grass", "color_b": "grass_d"}`
- `{"op": "scatter", "x": 0, "y": 0, "w": 32, "h": 32, "color": "grass_l", "target_color": "grass", "pattern": "noise|brick|wood|grass", "density": 0.2, "seed": 42}`
- `{"op": "stamp", "def": "sub_sprite", "x": 4, "y": 4, "flip_x": false, "flip_y": false, "angle": 45, "pivot": [4, 4], "remap": {"wood": "stone"}}`
- `{"op": "load_png", "path": "base.png", "x": 0, "y": 0, "crop": [0, 0, 16, 16]}`
- `{"op": "tilemap", "mode": "ortho|iso", "tile_w": 16, "tile_h": 16, "map": {"G": "grass_tile"}, "rows": ["GGG", "GGG"]}`
- `{"op": "autotile", "x": 0, "y": 0, "tile_size": 16, "inner": "water", "outer": "grass", "lip": "soil_d", "seed": 42}` (Generates 4x4 16-tile Wang bitmask atlas)
- `{"op": "char_rig", "x": 0, "y": 0, "size": 16, "dir": "down|up|left|right", "pose": "idle|walk|work", "frame": 0, "hat": "wheat", "shirt": "roof", "pants": "water_d"}` (Supports native sizes 16, 32, 64, 128 and direction-coherent work swings)
- `{"op": "mirror_x"}` / `{"op": "mirror_y"}`
- Top-level `"extends": "sprite.png | spec.json"` inherits palette, defs, and ops from an existing PNG or JSON!

## 2:1 Isometric Operations (`ops`)
- `{"op": "iso_tile", "cx": 32, "cy": 32, "rx": 16, "ry": 8, "color": "grass"}`
- `{"op": "iso_box", "cx": 32, "cy": 32, "rx": 12, "ry": 6, "h": 10, "top": "stone_l", "left": "stone", "right": "stone_d", "bevel": true, "ground_shadow": 2}`
- `{"op": "iso_roof", "cx": 32, "cy": 32, "rx": 12, "ry": 6, "h": 8, "style": "pyramid|gable_left|gable_right", "left": "roof_l", "right": "roof_d", "gable": "wood", "eave_shadow": true, "bevel": true}`
- `{"op": "iso_wall_rect", "face": "left|right", "x": 24, "y": 36, "w": 4, "h": 6, "color": "wood_d", "arch": true, "recessed": true}`
- `{"op": "iso_structure", "origin_x": 32, "origin_y": 30, "bevel": true, "ground_shadow": 2, "items": [{"type": "box|roof", "gx": 0, "gy": 0, "gz": 0, "rx": 8, "h": 10, ...}]}`
"""


def _print_diagnostics(frames: list, names: list[str]) -> None:
    seen: set[str] = set()
    for f, name in zip(frames, names):
        if f.clipped_pixels > 0:
            msg = f"[WARN] ({name}): {f.clipped_pixels} pixel(s) drawn out of canvas bounds."
            if msg not in seen:
                print(msg, file=sys.stderr)
                seen.add(msg)
        for w in f.warnings:
            msg = f"[WARN] ({name}): {w}"
            if msg not in seen:
                print(msg, file=sys.stderr)
                seen.add(msg)


def _cmd_render(args: argparse.Namespace) -> int:
    if args.spec == "-":
        raw = sys.stdin.read().lstrip("\ufeff")
    else:
        raw = Path(args.spec).read_text(encoding="utf-8-sig")
    spec = json.loads(raw)
    if args.lineless:
        spec["style"] = "lineless"
    else:
        spec.setdefault("style", "ext_outline")
    frames, names = run_frames(spec)
    _print_diagnostics(frames, names)

    out_path = Path(args.output)
    is_gif = out_path.suffix.lower() == ".gif"
    fps = args.fps or int(spec.get("fps", 8))
    cols = args.columns or spec.get("columns")

    if is_gif:
        out = export_gif(frames, out_path, fps=fps)
        print(f"Rendered GIF ({len(frames)} frames @ {fps}fps, {frames[0].width}x{frames[0].height}) -> {out}")
    elif args.sheet or len(frames) > 1 or args.godot:
        out = export_spritesheet(
            frames,
            out_path,
            frame_names=names,
            columns=cols,
            meta_path=args.meta,
            spec_json=json.dumps(spec),
        )
        print(f"Rendered spritesheet ({len(frames)} frames) -> {out}")
    else:
        out = export_png(frames[0], out_path, spec_json=json.dumps(spec))
        print(f"Rendered {frames[0].width}x{frames[0].height} -> {out}")

    if args.godot:
        tres_out = export_godot_tres(
            out_path, args.godot, frames, frame_names=names, columns=cols, fps=fps
        )
        print(f"Exported Godot 4 SpriteFrames -> {tres_out}")

    if args.layers_dir:
        layers = run_layers(spec)
        paths = export_layers(layers, args.layers_dir)
        print(f"Exported {len(paths)} layer PNGs -> {args.layers_dir}")

    if args.ascii:
        print(render_ascii(frames[0]))

    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    canvas = load_png_as_canvas(args.image)
    stats = analyze_canvas(canvas)
    print(json.dumps(stats, indent=2))
    if args.ascii:
        print(render_ascii(canvas))
    return 0


def _cmd_extract(args: argparse.Namespace) -> int:
    spec = extract_spec_from_png(args.image)
    print(json.dumps(spec, indent=2))
    return 0


def _cmd_guide(_args: argparse.Namespace) -> int:
    print(AGENT_GUIDE)
    print("## Built-in Palettes")
    for name, colors in list_palettes().items():
        keys = ", ".join(colors.keys())
        print(f"- `{name}` ({len(colors)} colors): keys = [{keys}]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pixelai",
        description="CLI-only deterministic pixel art & animation generator for AI agents.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    render_p = sub.add_parser(
        "render",
        help="Render PNG, spritesheet, or animated GIF from a JSON spec file or stdin ('-').",
        description=(
            "Render a pixel art PNG, spritesheet, or GIF from a declarative JSON spec.\n"
            "Run `pixelai guide` for full JSON DSL documentation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    render_p.add_argument(
        "spec",
        help="Path to JSON spec file, or '-' to read JSON from stdin.",
    )
    render_p.add_argument(
        "-o", "--output",
        required=True,
        help="Output file path (.png or .gif).",
    )
    render_p.add_argument(
        "--fps",
        type=int,
        default=None,
        help="Frames per second when exporting a .gif or Godot .tres (default: 8).",
    )
    render_p.add_argument(
        "--sheet",
        action="store_true",
        help="Force spritesheet export even for single-frame specs.",
    )
    render_p.add_argument(
        "--columns",
        type=int,
        default=None,
        help="Number of columns in exported spritesheet.",
    )
    render_p.add_argument(
        "--meta",
        default=None,
        help="Optional output path for spritesheet JSON metadata.",
    )
    render_p.add_argument(
        "--godot",
        default=None,
        help="Optional output path for Godot 4 SpriteFrames (.tres) resource.",
    )
    render_p.add_argument(
        "--layers-dir",
        default=None,
        help="Optional directory to export individual named layers as separate PNGs.",
    )
    render_p.add_argument(
        "--lineless",
        action="store_true",
        help="Render in Pure Lineless mode (no internal or external outlines).",
    )
    render_p.add_argument(
        "--ascii",
        action="store_true",
        help="Print ASCII luminance preview of the first frame to stdout.",
    )
    render_p.set_defaults(func=_cmd_render)

    inspect_p = sub.add_parser(
        "inspect",
        help="Inspect an existing PNG (bounding box, margins, color count, and optional ASCII preview).",
    )
    inspect_p.add_argument("image", help="Path to PNG file to inspect.")
    inspect_p.add_argument(
        "--ascii",
        action="store_true",
        help="Print ASCII luminance preview to stdout.",
    )
    inspect_p.set_defaults(func=_cmd_inspect)

    extract_p = sub.add_parser(
        "extract",
        help="Extract the embedded JSON spec from a PNG generated by pixelai.",
    )
    extract_p.add_argument("image", help="Path to PNG file.")
    extract_p.set_defaults(func=_cmd_extract)

    guide_p = sub.add_parser(
        "guide",
        help="Print complete LLM agent guide (all ops, isometric primitives, and palettes).",
    )
    guide_p.set_defaults(func=_cmd_guide)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

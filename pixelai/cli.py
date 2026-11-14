"""CLI entry point for pixelai-tools."""

import argparse
import json
import sys
from pathlib import Path

from pixelai import __version__
from pixelai.exporter import export_gif, export_png, export_spritesheet
from pixelai.palettes import list_palettes
from pixelai.runner import run_frames

AGENT_GUIDE = """# pixelai-tools — Agent Reference Guide

## CLI Usage
- Single PNG: `pixelai render spec.json -o out.png` (or `-` for stdin)
- Animated GIF: `pixelai render spec.json -o anim.gif --fps 8`
- Spritesheet + Metadata: `pixelai render spec.json -o sheet.png --sheet --columns 4 --meta sheet.json`

## JSON Spec Structure
```json
{
  "width": 32,
  "height": 32,
  "palette": "cozy24",
  "palette_ext": {"custom": "#ff8800"},
  "defs": {
    "sub_sprite": {"width": 8, "height": 8, "ops": [...]}
  },
  "ops": [...],
  "frames": [
    {"name": "idle_0", "ops": [...]},
    {"name": "idle_1", "ops": [...]}
  ],
  "post": [
    {"op": "shade", "amount": 0.2},
    {"op": "outline", "color": "ink"},
    {"op": "scale", "factor": 4}
  ]
}
```

## Drawing Operations (`ops`)
- `{"op": "pixel", "x": 0, "y": 0, "color": "ink"}`
- `{"op": "line", "x0": 0, "y0": 0, "x1": 5, "y1": 5, "color": "ink"}`
- `{"op": "rect", "x": 0, "y": 0, "w": 8, "h": 8, "color": "wood", "filled": true}`
- `{"op": "circle", "cx": 8, "cy": 8, "r": 4, "color": "grass", "filled": true}`
- `{"op": "polygon", "points": [[0,0], [8,4], [0,8]], "color": "roof", "filled": true}`
- `{"op": "fill", "x": 4, "y": 4, "color": "water"}`
- `{"op": "grid", "x": 0, "y": 0, "rows": ["..oo..", ".oggo."]}` (`.` and ` ` = transparent)
- `{"op": "dither", "x": 0, "y": 0, "w": 8, "h": 8, "color_a": "grass", "color_b": "grass_d"}`
- `{"op": "scatter", "x": 0, "y": 0, "w": 32, "h": 32, "color": "grass_l", "target_color": "grass", "pattern": "noise|brick|wood|grass", "density": 0.2, "seed": 42}`
- `{"op": "stamp", "def": "sub_sprite", "x": 4, "y": 4, "flip_x": false, "flip_y": false, "remap": {"wood": "stone"}}`
- `{"op": "tilemap", "tile_w": 16, "tile_h": 16, "map": {"G": "grass_tile"}, "rows": ["GGG", "GGG"]}`
- `{"op": "mirror_x"}` / `{"op": "mirror_y"}`

## 2:1 Isometric Operations (`ops`)
- `{"op": "iso_tile", "cx": 32, "cy": 32, "rx": 16, "ry": 8, "color": "grass", "border": "grass_d"}`
- `{"op": "iso_box", "cx": 32, "cy": 32, "rx": 12, "ry": 6, "h": 10, "top": "stone_l", "left": "stone", "right": "stone_d", "edge": "ink"}`
- `{"op": "iso_roof", "cx": 32, "cy": 32, "rx": 13, "ry": 6, "h": 8, "style": "pyramid|gable_left|gable_right", "left": "roof_l", "right": "roof_d", "gable": "wood", "ridge": "ink"}`
- `{"op": "iso_wall_rect", "face": "left|right", "x": 24, "y": 36, "w": 4, "h": 6, "color": "ink"}`
"""


def _cmd_render(args: argparse.Namespace) -> int:
    if args.spec == "-":
        raw = sys.stdin.read().lstrip("\ufeff")
    else:
        raw = Path(args.spec).read_text(encoding="utf-8-sig")
    spec = json.loads(raw)
    frames, names = run_frames(spec)

    out_path = Path(args.output)
    is_gif = out_path.suffix.lower() == ".gif"

    if is_gif:
        fps = args.fps or int(spec.get("fps", 8))
        out = export_gif(frames, out_path, fps=fps)
        print(f"Rendered GIF ({len(frames)} frames @ {fps}fps, {frames[0].width}x{frames[0].height}) -> {out}")
    elif args.sheet or len(frames) > 1:
        cols = args.columns or spec.get("columns")
        out = export_spritesheet(
            frames, out_path, frame_names=names, columns=cols, meta_path=args.meta
        )
        print(f"Rendered spritesheet ({len(frames)} frames) -> {out}")
    else:
        out = export_png(frames[0], out_path)
        print(f"Rendered {frames[0].width}x{frames[0].height} -> {out}")
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
        help="Frames per second when exporting a .gif (default: 8).",
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
    render_p.set_defaults(func=_cmd_render)

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

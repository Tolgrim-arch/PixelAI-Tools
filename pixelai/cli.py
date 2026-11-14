"""CLI entry point for pixelai-tools."""

import argparse
import json
import sys
from pathlib import Path

from pixelai import __version__
from pixelai.exporter import export_png
from pixelai.runner import run_spec


def _cmd_render(args: argparse.Namespace) -> int:
    if args.spec == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(args.spec).read_text(encoding="utf-8")
    spec = json.loads(raw)
    canvas = run_spec(spec)
    out = export_png(canvas, args.output)
    print(f"Rendered {canvas.width}x{canvas.height} -> {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pixelai",
        description="CLI-only deterministic pixel art generator for AI agents.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    render_p = sub.add_parser(
        "render",
        help="Render a pixel art sprite from a JSON spec file or stdin ('-').",
        description=(
            "Render a pixel art PNG from a declarative JSON spec.\n"
            "Ops: pixel, line, rect, circle, fill, mirror_x, mirror_y.\n"
            "Post: outline, scale."
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
        help="Output PNG file path.",
    )
    render_p.set_defaults(func=_cmd_render)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

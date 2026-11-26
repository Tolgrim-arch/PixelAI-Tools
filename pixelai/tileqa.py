"""Spatial tile diagnostics and legal Wang neighborhoods for visual review."""

import json
from pathlib import Path
import random
import tempfile

from PIL import Image


def _edge_difference(first, second, axis):
    if axis == "horizontal":
        pairs = [(first.getpixel((first.width-1, y)), second.getpixel((0, y))) for y in range(first.height)]
    else:
        pairs = [(first.getpixel((x, first.height-1)), second.getpixel((x, 0))) for x in range(first.width)]
    # Compare premultiplied RGBA, so RGB stored beneath transparency is irrelevant.
    def rgba(color):
        return [color[channel] * color[3] / 255 for channel in range(3)] + [color[3]]
    return round(sum(sum(abs(a-b) for a, b in zip(rgba(left), rgba(right))) / 4 for left, right in pairs) / len(pairs), 3)


def legal_neighbor(first, second, axis):
    if axis == "horizontal":
        return bool(first & 2) == bool(second & 1) and bool(first & 4) == bool(second & 8)
    return bool(first & 8) == bool(second & 1) and bool(first & 4) == bool(second & 2)


def diagnose_tiles(source, output, mode="repeat", tile_size=None, seed=42):
    if mode not in ("repeat", "wang16"):
        raise ValueError("Tile diagnostic mode must be repeat or wang16")
    with Image.open(source) as image:
        texture = image.convert("RGBA")
    if mode == "wang16":
        if type(tile_size) is not int or tile_size < 4 or texture.size != (tile_size * 4, tile_size * 4):
            raise ValueError("wang16 requires a 4x4 atlas and explicit tile_size >= 4")
        tiles = [texture.crop(((i % 4) * tile_size, (i // 4) * tile_size,
                               (i % 4 + 1) * tile_size, (i // 4 + 1) * tile_size)) for i in range(16)]
        rng = random.Random(seed)
        corners = [[rng.randrange(2) for _ in range(9)] for _ in range(9)]
        masks = [[corners[y][x] + 2*corners[y][x+1] + 4*corners[y+1][x+1] + 8*corners[y+1][x]
                  for x in range(8)] for y in range(8)]
    else:
        tiles, masks = [texture], [[0] * 8 for _ in range(8)]
    width, height = tiles[0].size
    mosaic = Image.new("RGBA", (width * 8, height * 8))
    for y, row in enumerate(masks):
        for x, mask in enumerate(row):
            mosaic.paste(tiles[mask], (x * width, y * height))
    seams = []
    for axis in ("horizontal", "vertical"):
        for first in range(len(tiles)):
            for second in range(len(tiles)):
                if mode == "repeat" or legal_neighbor(first, second, axis):
                    seams.append({"axis": axis, "first": first, "second": second,
                                  "mean_edge_delta": _edge_difference(tiles[first], tiles[second], axis)})
    report = {"schema_version": 1, "mode": mode, "seed": seed, "status": "needs_visual_review",
              "tile_dimensions": [width, height], "sampled_masks": masks, "legal_seams": seams,
              "warning": "Edge deltas are diagnostic, not a seamlessness verdict; inspect structural and material continuity.",
              "unverified": ["visual continuity", "repetition quality", "temporal seams", "blob47 coverage"]}
    destination = Path(output).resolve()
    if destination.exists():
        raise ValueError("Tile diagnostic output directory already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pixelai-tiles-", dir=destination.parent) as temporary:
        bundle = Path(temporary) / "bundle"
        bundle.mkdir()
        mosaic.save(bundle / "mosaic.png")
        mosaic.resize((mosaic.width * 4, mosaic.height * 4), Image.Resampling.NEAREST).save(bundle / "mosaic_4x.png")
        for axis in ("horizontal", "vertical"):
            comparisons = [seam for seam in seams if seam["axis"] == axis]
            cell_w, cell_h = (width * 2, height) if axis == "horizontal" else (width, height * 2)
            columns = min(8, len(comparisons))
            rows = (len(comparisons) + columns - 1) // columns
            sheet = Image.new("RGBA", (columns * (cell_w + 2) + 2, rows * (cell_h + 2) + 2), "#303038")
            filename = f"pairs_{axis}.png"
            for index, seam in enumerate(comparisons):
                x, y = 2 + (index % columns) * (cell_w + 2), 2 + (index // columns) * (cell_h + 2)
                sheet.paste(tiles[seam["first"]], (x, y))
                sheet.paste(tiles[seam["second"]], (x + width, y) if axis == "horizontal" else (x, y + height))
                seam["comparison"] = {"image": filename, "rect": [x, y, cell_w, cell_h]}
            sheet.save(bundle / filename)
        (bundle / "seams.json").write_text(json.dumps(report, indent=2))
        bundle.rename(destination)
    return {**report, "output": str(destination)}


def register(sub):
    parser = sub.add_parser("tilecheck", help="Create a repetition mosaic and seam diagnostics, including all legal Wang16 edge pairs.")
    parser.add_argument("source")
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=("repeat", "wang16"), default="repeat")
    parser.add_argument("--tile-size", type=int)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json", action="store_true")

    def run(args):
        print(json.dumps(diagnose_tiles(args.source, args.output, args.mode, args.tile_size, args.seed)))
        return 0

    parser.set_defaults(func=run)

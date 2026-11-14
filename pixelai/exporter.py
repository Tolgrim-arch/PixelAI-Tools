"""Exporters for pixel art canvases, spritesheets, and GIF animations."""

import json
import math
from pathlib import Path
from PIL import Image
from pixelai.canvas import Canvas


def _canvas_to_image(canvas: Canvas) -> Image.Image:
    img = Image.new("RGBA", (canvas.width, canvas.height))
    img.putdata(canvas.pixels)
    return img


def export_png(canvas: Canvas, path: str | Path) -> Path:
    """Export a single Canvas to a lossless RGBA PNG file."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _canvas_to_image(canvas).save(out_path, format="PNG")
    return out_path


def export_gif(
    frames: list[Canvas], path: str | Path, fps: int = 8
) -> Path:
    """Export a list of Canvases as a looping animated GIF."""
    if not frames:
        raise ValueError("Cannot export GIF with zero frames")
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = max(20, int(round(1000 / max(1, fps))))
    images = [_canvas_to_image(f) for f in frames]
    images[0].save(
        out_path,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
    )
    return out_path


def export_spritesheet(
    frames: list[Canvas],
    path: str | Path,
    frame_names: list[str] | None = None,
    columns: int | None = None,
    meta_path: str | Path | None = None,
) -> Path:
    """Pack multiple Canvases into a spritesheet PNG and optional JSON metadata."""
    if not frames:
        raise ValueError("Cannot export spritesheet with zero frames")
    fw, fh = frames[0].width, frames[0].height
    cols = columns if (columns and columns > 0) else len(frames)
    rows = math.ceil(len(frames) / cols)

    sheet = Image.new("RGBA", (fw * cols, fh * rows), (0, 0, 0, 0))
    meta_frames = []
    for idx, frame in enumerate(frames):
        col = idx % cols
        row = idx // cols
        x, y = col * fw, row * fh
        sheet.paste(_canvas_to_image(frame), (x, y))
        name = (
            frame_names[idx]
            if frame_names and idx < len(frame_names)
            else f"frame_{idx}"
        )
        meta_frames.append({"name": name, "x": x, "y": y, "w": fw, "h": fh})

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, format="PNG")

    if meta_path:
        mp = Path(meta_path)
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(
            json.dumps(
                {
                    "tile_width": fw,
                    "tile_height": fh,
                    "columns": cols,
                    "rows": rows,
                    "frames": meta_frames,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return out_path


def export_godot_tres(
    sheet_path: str | Path,
    tres_path: str | Path,
    frames: list[Canvas],
    frame_names: list[str] | None = None,
    columns: int | None = None,
    fps: int = 8,
) -> Path:
    """Export a Godot 4 SpriteFrames .tres resource referencing the spritesheet PNG."""
    if not frames:
        raise ValueError("Cannot export Godot .tres with zero frames")
    fw, fh = frames[0].width, frames[0].height
    cols = columns if (columns and columns > 0) else len(frames)
    sheet_name = Path(sheet_path).name

    lines = [
        f'[gd_resource type="SpriteFrames" load_steps={len(frames) + 2} format=3]',
        "",
        f'[ext_resource type="Texture2D" path="res://{sheet_name}" id="1_tex"]',
        "",
    ]
    frame_refs = []
    for idx in range(len(frames)):
        col = idx % cols
        row = idx // cols
        x, y = col * fw, row * fh
        sub_id = f"AtlasTexture_{idx}"
        lines.extend([
            f'[sub_resource type="AtlasTexture" id="{sub_id}"]',
            'atlas = ExtResource("1_tex")',
            f"region = Rect2({x}, {y}, {fw}, {fh})",
            "",
        ])
        frame_refs.append(f'{{"duration": 1.0, "texture": SubResource("{sub_id}")}}')

    _ = frame_names
    lines.extend([
        "[resource]",
        "animations = [{",
        f'"frames": [{", ".join(frame_refs)}],',
        '"loop": true,',
        '"name": &"default",',
        f'"speed": {float(fps):.1f}',
        "}]",
        "",
    ])
    out = Path(tres_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out

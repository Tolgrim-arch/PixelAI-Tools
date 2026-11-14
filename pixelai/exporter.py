"""Exporters for pixel art canvases, spritesheets, Godot .tres, and GIF animations."""

import json
import math
from pathlib import Path
from typing import Any
from PIL import Image, PngImagePlugin
from pixelai.canvas import Canvas


def _canvas_to_image(canvas: Canvas) -> Image.Image:
    img = Image.new("RGBA", (canvas.width, canvas.height))
    img.putdata(canvas.pixels)
    return img


def _build_pnginfo(spec_json: str | None) -> PngImagePlugin.PngInfo | None:
    if not spec_json:
        return None
    info = PngImagePlugin.PngInfo()
    info.add_text("pixelai_spec", spec_json)
    return info


def extract_spec_from_png(path: str | Path) -> dict[str, Any]:
    """Extract the embedded pixelai JSON spec from a PNG's tEXt metadata."""
    with Image.open(path) as img:
        raw = img.info.get("pixelai_spec")
    if not raw:
        raise ValueError(f"No embedded pixelai_spec found in {path}")
    return json.loads(raw)


def _rgba_to_gif_frame(img: Image.Image) -> Image.Image:
    """Convert an RGBA image into a P-mode GIF frame with index 0 reserved for transparency."""
    alpha = img.getchannel("A")
    rgb = img.convert("RGB").quantize(colors=255, method=Image.Quantize.FASTOCTREE)
    pal = rgb.getpalette() or [0] * 768
    # Shift palette indices by +1 so index 0 is dedicated to transparent
    shifted_pal = [0, 0, 0] + pal[: 255 * 3]
    out = Image.new("P", img.size, 0)
    out.putpalette(shifted_pal)

    getter = getattr(rgb, "get_flattened_data", rgb.getdata)
    a_getter = getattr(alpha, "get_flattened_data", alpha.getdata)
    out.putdata([
        (px + 1) if a >= 128 else 0
        for px, a in zip(getter(), a_getter())
    ])
    return out


def export_png(
    canvas: Canvas, path: str | Path, spec_json: str | None = None
) -> Path:
    """Export a single Canvas to a lossless RGBA PNG file (with optional embedded spec)."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _canvas_to_image(canvas).save(
        out_path, format="PNG", pnginfo=_build_pnginfo(spec_json)
    )
    return out_path


def export_gif(
    frames: list[Canvas], path: str | Path, fps: int = 8
) -> Path:
    """Export a list of Canvases as a clean transparent looping animated GIF."""
    if not frames:
        raise ValueError("Cannot export GIF with zero frames")
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = max(20, int(round(1000 / max(1, fps))))
    p_frames = [_rgba_to_gif_frame(_canvas_to_image(f)) for f in frames]
    p_frames[0].save(
        out_path,
        format="GIF",
        save_all=True,
        append_images=p_frames[1:],
        duration=duration_ms,
        loop=0,
        transparency=0,
        disposal=2,
    )
    return out_path


def export_spritesheet(
    frames: list[Canvas],
    path: str | Path,
    frame_names: list[str] | None = None,
    columns: int | None = None,
    meta_path: str | Path | None = None,
    spec_json: str | None = None,
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
    sheet.save(out_path, format="PNG", pnginfo=_build_pnginfo(spec_json))

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


def export_layers(
    layers: list[tuple[str, Canvas]], layers_dir: str | Path
) -> list[Path]:
    """Export named layers as individual numbered PNG files for Aseprite/Photoshop editing."""
    out_dir = Path(layers_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for idx, (name, canvas) in enumerate(layers):
        safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)
        p = out_dir / f"{idx:02d}_{safe_name}.png"
        export_png(canvas, p)
        paths.append(p)
    return paths


def export_showcase(
    sources: list[str | Path],
    out_path: str | Path,
    scale: int = 4,
    columns: int = 4,
    fps: int = 8,
) -> Path:
    """Build an Itch.io showcase sheet (.png) or animated pack banner (.gif) from sprites/GIFs."""
    from PIL import ImageDraw, ImageSequence

    out = Path(out_path).resolve()
    files: list[Path] = []
    for s in sources:
        p = Path(s)
        if p.is_dir():
            files.extend(
                sorted(
                    f
                    for f in p.iterdir()
                    if f.suffix.lower() in (".gif", ".png")
                    and not f.stem.lower().startswith("itch_showcase")
                    and f.resolve() != out
                )
            )
        elif p.exists() and p.resolve() != out:
            files.append(p)
    if not files:
        raise ValueError("No valid .png or .gif files found for showcase")

    loaded: list[list[Image.Image]] = []
    max_w, max_h, max_frames = 16, 16, 1
    for f in files:
        with Image.open(f) as im:
            raw_seq = [
                (fr.convert("RGBA"), int(fr.info.get("duration", 0) or 0))
                for fr in ImageSequence.Iterator(im)
            ]
            valid_durs = [d for _, d in raw_seq if d > 0]
            min_dur = min(valid_durs) if valid_durs else 0
            seq: list[Image.Image] = []
            for img_fr, dur in raw_seq:
                repeats = max(1, int(round(dur / min_dur))) if (min_dur > 0 and dur > 0) else 1
                for _ in range(repeats):
                    seq.append(img_fr.copy() if len(seq) > 0 else img_fr)
            loaded.append(seq)
            max_w = max(max_w, seq[0].width)
            max_h = max(max_h, seq[0].height)
            max_frames = max(max_frames, len(seq))

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cell_w = (max_w + 4) * scale
    cell_h = (max_h + 4) * scale
    bg_col = (34, 32, 42, 255)
    card_col = (46, 43, 56, 255)
    border_col = (68, 63, 82, 255)

    if out.suffix.lower() == ".gif":
        cols = max(1, min(columns, len(loaded)))
        rows = math.ceil(len(loaded) / cols)
        total_t = max(12, max_frames)
        gif_frames: list[Image.Image] = []
        for t in range(total_t):
            sheet = Image.new("RGBA", (cols * cell_w + 8, rows * cell_h + 8), bg_col)
            draw = ImageDraw.Draw(sheet)
            for idx, seq in enumerate(loaded):
                c, r = idx % cols, idx // cols
                x0, y0 = 4 + c * cell_w, 4 + r * cell_h
                draw.rectangle([x0 + 2, y0 + 2, x0 + cell_w - 3, y0 + cell_h - 3], fill=card_col, outline=border_col)
                fr = seq[t % len(seq)]
                up = fr.resize((fr.width * scale, fr.height * scale), Image.Resampling.NEAREST)
                px = x0 + (cell_w - up.width) // 2
                py = y0 + (cell_h - up.height) // 2
                sheet.paste(up, (px, py), up)
            gif_frames.append(_rgba_to_gif_frame(sheet))
        duration_ms = max(20, int(round(1000 / max(1, fps))))
        gif_frames[0].save(
            out, format="GIF", save_all=True, append_images=gif_frames[1:], duration=duration_ms, loop=0
        )
        return out

    # PNG contact sheet: each asset is a row showing all its animation frames
    sheet = Image.new("RGBA", (max_frames * cell_w + 8, len(loaded) * cell_h + 8), bg_col)
    draw = ImageDraw.Draw(sheet)
    for row_idx, seq in enumerate(loaded):
        for col_idx, fr in enumerate(seq):
            x0, y0 = 4 + col_idx * cell_w, 4 + row_idx * cell_h
            draw.rectangle([x0 + 2, y0 + 2, x0 + cell_w - 3, y0 + cell_h - 3], fill=card_col, outline=border_col)
            up = fr.resize((fr.width * scale, fr.height * scale), Image.Resampling.NEAREST)
            px = x0 + (cell_w - up.width) // 2
            py = y0 + (cell_h - up.height) // 2
            sheet.paste(up, (px, py), up)
    sheet.save(out, format="PNG")
    return out

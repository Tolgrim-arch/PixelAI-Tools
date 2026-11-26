"""Verify exported construction against its procedural source and timing."""

import json
from pathlib import Path
import tempfile

from PIL import Image, ImageSequence

from pixelai.animation_contract import clips_by_index, durations_ms
from pixelai.exporter import export_gif
from pixelai.manifest import load_manifest
from pixelai.runner import _resolve_extends, resolve_spec_paths, run_frames
from pixelai.schema import validate_managed_fields


def _pixels(image):
    image = image.convert("RGBA")
    values = getattr(image, "get_flattened_data", image.getdata)()
    return [pixel if pixel[3] else (0, 0, 0, 0) for pixel in values]


def _matches(image, canvas):
    normalized = [pixel if pixel[3] else (0, 0, 0, 0) for pixel in canvas.pixels]
    return image.size == (canvas.width, canvas.height) and _pixels(image) == normalized


def _gif_sequence(path):
    with Image.open(path) as image:
        loop = image.info.get("loop")
        frames = [(frame.size, _pixels(frame), frame.info.get("duration"))
                  for frame in ImageSequence.Iterator(image)]
        return loop, frames


def verify_construction(project, submission, native_size=None):
    """Validate source-to-pixel provenance for PNG, atlas PNG and GIF previews."""
    root = Path(project).resolve()
    evidence = {record["path"] for record in submission["evidence"]}
    source_name, image_name = submission.get("source_path"), submission.get("image_path")
    if not isinstance(source_name, str) or not isinstance(image_name, str) or source_name not in evidence or image_name not in evidence:
        raise ValueError("source_path and image_path must identify submitted source and image evidence")
    source_path, image_path = root / source_name, root / image_name
    if not source_path.resolve().is_relative_to(root) or not image_path.resolve().is_relative_to(root):
        raise ValueError("Construction inputs must stay inside the project")
    spec = json.loads(source_path.read_text(encoding="utf-8-sig"))
    if not isinstance(spec, dict):
        raise ValueError("Source specification must be an object")
    validate_managed_fields(spec)
    spec.setdefault("style", "ext_outline")
    spec["fresh"] = True
    expanded = _resolve_extends(resolve_spec_paths(spec, source_path.parent))
    validate_managed_fields(expanded)
    frames, _ = run_frames(expanded)
    if native_size is not None and any([frame.width, frame.height] != native_size for frame in frames):
        raise ValueError("Rendered frame dimensions violate the managed native_size contract")
    fps = spec.get("fps", 8)
    timings = durations_ms(len(frames), fps, spec.get("durations_ms"))
    clips = clips_by_index(len(frames), spec.get("clips"))
    if image_path.suffix.lower() == ".gif":
        with tempfile.TemporaryDirectory(prefix="pixelai-provenance-") as directory:
            expected = Path(directory) / "expected.gif"
            export_gif(frames, expected, fps=fps, durations_ms=timings)
            if _gif_sequence(image_path) != _gif_sequence(expected):
                raise ValueError("GIF pixels or timing do not match the submitted source")
        return
    if image_path.suffix.lower() != ".png":
        raise ValueError("Managed construction supports native PNG, atlas PNG and GIF previews")
    manifest_name = submission.get("manifest_path")
    if manifest_name is None:
        if len(frames) != 1:
            raise ValueError("Animated PNG construction requires manifest_path evidence")
        with Image.open(image_path) as image:
            if not _matches(image, frames[0]):
                raise ValueError("Rendered image does not match the submitted source specification")
        return
    if not isinstance(manifest_name, str) or manifest_name not in evidence:
        raise ValueError("manifest_path must identify submitted manifest evidence")
    manifest_path = root / manifest_name
    if not manifest_path.resolve().is_relative_to(root):
        raise ValueError("Manifest must stay inside the project")
    manifest, texture = load_manifest(manifest_path)
    if (manifest_path.parent / manifest["texture"]).resolve() != image_path.resolve():
        raise ValueError("Manifest texture must be the submitted construction image")
    if len(manifest["frames"]) != len(frames):
        raise ValueError("Manifest frame count does not match the source")
    for index, (record, expected) in enumerate(zip(manifest["frames"], frames)):
        x, y, width, height = record["rect"]
        image = texture.crop((x, y, x + width, y + height))
        if not _matches(image, expected):
            raise ValueError(f"Atlas frame {index} does not match the source")
        if record["duration_ms"] != timings[index]:
            raise ValueError(f"Atlas frame {index} duration does not match the source")
        runtime = [item for item in expected.attachments if item.get("type") == "runtime"]
        if runtime:
            for field in ("pivot", "ground_anchor", "sort_origin", "regions", "sockets", "view", "action", "state"):
                default = [] if field == "regions" else {} if field == "sockets" else None
                if record.get(field, default) != runtime[0].get(field, default):
                    raise ValueError(f"Atlas frame {index} runtime {field} does not match the source")
    ids = [frame["id"] for frame in manifest["frames"]]
    expected_clips = {name: {"frames": [ids[index] for index in clip["frames"]], "loop": clip["loop"],
                            **({"interruptible": clip["interruptible"]} if "interruptible" in clip else {})}
                      for name, clip in clips.items()}
    if manifest["clips"] != expected_clips:
        raise ValueError("Manifest clips do not match the source actions")
    if "transitions" in spec and manifest.get("transitions", []) != spec["transitions"]:
        raise ValueError("Manifest transitions do not match the source")

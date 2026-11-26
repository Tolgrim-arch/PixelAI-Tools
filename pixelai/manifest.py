"""Universal exported asset contract and deterministic playback inspection.

Coordinates use the untrimmed native canvas, X right and Y down. Atlas
rectangles use texture coordinates; pivots and sockets use canvas coordinates.
"""

import hashlib
import json
import math
from pathlib import Path

from PIL import Image
from pixelai.geometry import validate_polygon
from pixelai.animation_contract import validate_transitions


def build_manifest(spec, frames, texture_path, manifest_path, columns, timings, clips):
    """Build a universal manifest from actual rendered frames and explicit runtime data."""
    texture_path, manifest_path = Path(texture_path).resolve(), Path(manifest_path).resolve()
    if not texture_path.is_relative_to(manifest_path.parent):
        raise ValueError("Manifest texture must be inside the manifest directory")
    asset_id = spec.get("asset_id")
    if not isinstance(asset_id, str) or not asset_id.strip():
        raise ValueError("Universal manifest export requires spec.asset_id")
    columns = columns or len(frames)
    records = []
    for index, frame in enumerate(frames):
        if (frame.width, frame.height) != (frames[0].width, frames[0].height):
            raise ValueError("Universal atlas frames must have consistent dimensions")
        if not any(pixel[3] for pixel in frame.pixels):
            raise ValueError("Universal atlas frames cannot be empty")
        runtime = [item for item in frame.attachments if item.get("type") == "runtime"]
        if len(runtime) != 1:
            raise ValueError("Universal manifest export requires explicit spec.runtime coordinates")
        record = {key: value for key, value in runtime[0].items() if key != "type"}
        for name in ("pivot", "ground_anchor", "sort_origin"):
            x, y = _point(record.get(name), f"runtime.{name}")
            if not 0 <= x <= frame.width or not 0 <= y <= frame.height:
                raise ValueError(f"runtime.{name} is outside the rendered frame")
        record.update(id=str(index), rect=[index % columns * frame.width, index // columns * frame.height, frame.width, frame.height], duration_ms=timings[index])
        records.append(record)
    return {"schema_version": 1, "asset_id": asset_id,
            "texture": texture_path.relative_to(manifest_path.parent).as_posix(),
            "frames": records,
            "clips": {name: {**clip, "frames": [str(index) for index in clip["frames"]]} for name, clip in clips.items()},
            "transitions": validate_transitions(spec.get("transitions", []), clips)}


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _point(value, name):
    if not isinstance(value, list) or len(value) != 2 or any(
        type(v) not in (int, float) or not math.isfinite(v) for v in value
    ):
        raise ValueError(f"{name} must contain two finite numbers")
    return value


def load_manifest(source):
    """Read and validate actual exported pixels, regions, timing and state links."""
    path = Path(source).resolve()
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Manifest requires schema_version 1")
    if not isinstance(data.get("asset_id"), str) or not data["asset_id"].strip():
        raise ValueError("Manifest requires asset_id")
    texture = data.get("texture")
    if not isinstance(texture, str) or Path(texture).is_absolute():
        raise ValueError("texture must be a relative file path")
    image_path = (path.parent / texture).resolve()
    if not image_path.is_relative_to(path.parent):
        raise ValueError("texture must be inside the manifest directory")
    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
    if data.get("texture_sha256") != digest:
        raise ValueError("Texture hash is missing or stale")
    with Image.open(image_path) as source_image:
        image = source_image.convert("RGBA")
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("frames must be a nonempty array")
    frame_ids = set()
    for frame in frames:
        if not isinstance(frame, dict) or not isinstance(frame.get("id"), str) or not frame["id"]:
            raise ValueError("Each frame requires an id")
        if frame["id"] in frame_ids:
            raise ValueError("Frame ids must be unique")
        frame_ids.add(frame["id"])
        rect = frame.get("rect")
        if not isinstance(rect, list) or len(rect) != 4:
            raise ValueError("frame.rect must be [x,y,width,height]")
        x, y, w, h = [_integer(v, "frame.rect", 1 if i > 1 else 0) for i, v in enumerate(rect)]
        if x + w > image.width or y + h > image.height:
            raise ValueError("Frame rectangle is outside the texture")
        if not image.crop((x, y, x + w, y + h)).getchannel("A").getbbox():
            raise ValueError("Exported frame is empty")
        _integer(frame.get("duration_ms"), "frame.duration_ms", 1)
        for name in ("pivot", "ground_anchor", "sort_origin"):
            px, py = _point(frame.get(name), f"frame.{name}")
            if not 0 <= px <= w or not 0 <= py <= h:
                raise ValueError(f"frame.{name} must be inside the native canvas")
        sockets = frame.get("sockets", {})
        if not isinstance(sockets, dict):
            raise ValueError("frame.sockets must be an object")
        for name, point in sockets.items():
            _point(point, f"socket.{name}")
        regions = frame.get("regions", [])
        if not isinstance(regions, list):
            raise ValueError("frame.regions must be an array")
        region_ids = set()
        for region in regions:
            if not isinstance(region, dict) or not isinstance(region.get("id"), str) or not region["id"] or region["id"] in region_ids:
                raise ValueError("Frame regions require unique nonempty ids")
            region_ids.add(region["id"])
            if region.get("role") not in ("collision", "hit", "hurt", "interaction", "occluder"):
                raise ValueError("Region requires a supported functional role")
            validate_polygon(region.get("polygon"))
    clips = data.get("clips")
    if not isinstance(clips, dict) or not clips:
        raise ValueError("clips must be a nonempty object")
    for name, clip in clips.items():
        if not isinstance(clip, dict) or type(clip.get("loop")) is not bool:
            raise ValueError(f"clip {name} requires an explicit loop boolean")
        if "interruptible" in clip and type(clip["interruptible"]) is not bool:
            raise ValueError("clip.interruptible must be a boolean")
        sequence = clip.get("frames")
        if not isinstance(sequence, list) or not sequence or any(f not in frame_ids for f in sequence):
            raise ValueError(f"clip {name} references missing frames")
    validate_transitions(data.get("transitions", []), clips)
    return data, image


def simulate(source):
    """Inspect exported playback only; this is not a full physics simulator."""
    data, image = load_manifest(source)
    frames = {f["id"]: f for f in data["frames"]}
    traces = []
    for name, clip in data["clips"].items():
        elapsed = 0
        for frame_id in clip["frames"]:
            frame = frames[frame_id]
            traces.append({"clip": name, "frame": frame_id, "start_ms": elapsed,
                           "duration_ms": frame["duration_ms"], "pivot": frame["pivot"],
                           "ground_anchor": frame["ground_anchor"], "sort_origin": frame["sort_origin"]})
            elapsed += frame["duration_ms"]
    return {"schema_version": 1, "asset_id": data["asset_id"], "status": "validated",
            "verification_scope": "exported regions, content identity, timing and state references",
            "unverified": ["collision behavior", "sorting behavior", "visual readability", "acting", "tile continuity", "engine integration"],
            "texture_size": list(image.size), "trace": traces}


def register(sub):
    parser = sub.add_parser("simulate", help="Validate a universal manifest and trace exported clip timing (experimental).")
    parser.add_argument("manifest")
    parser.add_argument("--json", action="store_true")

    def run(args):
        print(json.dumps(simulate(args.manifest)))
        return 0

    parser.set_defaults(func=run)

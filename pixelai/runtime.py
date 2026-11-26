"""Reference scene playback using only exported manifests and textures."""

import json
from pathlib import Path
import tempfile

from PIL import Image, ImageDraw

from pixelai.manifest import _integer, _point, load_manifest
from pixelai.geometry import overlap, world_regions


def frame_at(data, clip_name, time_ms):
    if clip_name not in data["clips"]:
        raise ValueError(f"Missing clip: {clip_name}")
    frames = {frame["id"]: frame for frame in data["frames"]}
    clip = data["clips"][clip_name]
    sequence = [frames[name] for name in clip["frames"]]
    duration = sum(frame["duration_ms"] for frame in sequence)
    remaining = time_ms % duration if clip["loop"] else min(time_ms, duration - 1)
    for frame in sequence:
        if remaining < frame["duration_ms"]:
            return frame
        remaining -= frame["duration_ms"]
    raise ValueError("Invalid clip timing")


def actor_track(actor, data):
    """Resolve explicit state changes; undeclared or early transitions fail."""
    timeline = actor.get("timeline", [])
    if not isinstance(timeline, list):
        raise ValueError("actor.timeline must be an array")
    track = [{"at_ms": 0, "clip": actor["clip"], "clip_started_ms": 0, "position": actor["position"]}]
    transitions = {(edge["from"], edge["to"]) for edge in data.get("transitions", [])}
    durations = {clip: sum(next(f["duration_ms"] for f in data["frames"] if f["id"] == frame) for frame in definition["frames"])
                 for clip, definition in data["clips"].items()}
    previous_time = -1
    for event in timeline:
        if not isinstance(event, dict) or set(event) - {"at_ms", "clip", "position"}:
            raise ValueError("Timeline events accept at_ms, clip and position only")
        at = _integer(event.get("at_ms"), "timeline.at_ms")
        if at <= previous_time:
            raise ValueError("Timeline times must be strictly increasing")
        previous_time = at
        state = dict(track[-1])
        state["at_ms"] = at
        if "position" in event:
            position = _point(event["position"], "timeline.position")
            if any(type(value) is not int for value in position):
                raise ValueError("Timeline positions must use native integer pixels")
            state["position"] = position
        if "clip" in event:
            target = event["clip"]
            if not isinstance(target, str) or target not in data["clips"]:
                raise ValueError("Timeline references a missing clip")
            current = state["clip"]
            if target != current and (current, target) not in transitions:
                raise ValueError(f"Undeclared transition: {current} -> {target}")
            if not data["clips"][current].get("interruptible", True) and at - state["clip_started_ms"] < durations[current]:
                raise ValueError("Timeline interrupts a protected action before completion")
            state["clip"] = target
            state["clip_started_ms"] = at
        track.append(state)
    return track


def render_scene(source, output):
    """Produce native contextual frames and sorting traces; no quality approval."""
    scene_path = Path(source).resolve()
    scene = json.loads(scene_path.read_text())
    if not isinstance(scene, dict) or scene.get("schema_version") != 1:
        raise ValueError("Scene requires schema_version 1")
    width = _integer(scene.get("width"), "scene.width", 1)
    height = _integer(scene.get("height"), "scene.height", 1)
    times = scene.get("times_ms")
    if not isinstance(times, list) or not times:
        raise ValueError("Scene requires nonempty times_ms")
    for time in times:
        _integer(time, "time_ms")
    actors = scene.get("actors")
    if not isinstance(actors, list) or not actors:
        raise ValueError("Scene requires actors")
    loaded, identities = [], set()
    for actor in actors:
        if not isinstance(actor, dict) or not isinstance(actor.get("id"), str) or not actor["id"] or actor["id"] in identities:
            raise ValueError("Actors require unique nonempty ids")
        identities.add(actor["id"])
        position = _point(actor.get("position"), "actor.position")
        if any(type(value) is not int for value in position):
            raise ValueError("Reference scene positions must use native integer pixels")
        manifest = actor.get("manifest")
        if not isinstance(manifest, str) or Path(manifest).is_absolute():
            raise ValueError("Actor manifest must be scene-relative")
        path = (scene_path.parent / manifest).resolve()
        if not path.is_relative_to(scene_path.parent):
            raise ValueError("Actor manifest must remain inside the scene directory")
        data, image = load_manifest(path)
        if actor.get("clip") not in data["clips"]:
            raise ValueError("Actor must select an existing clip")
        loaded.append((actor, data, image, actor_track(actor, data)))
    destination = Path(output).resolve()
    if destination.exists():
        raise ValueError("Scene output directory already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    trace = []
    with tempfile.TemporaryDirectory(prefix="pixelai-scene-", dir=destination.parent) as temporary:
        bundle = Path(temporary) / "bundle"
        bundle.mkdir()
        for index, time in enumerate(times):
            canvas = Image.new("RGBA", (width, height), scene.get("background", "#404048"))
            posed = []
            for actor, data, image, track in loaded:
                state = next(state for state in reversed(track) if state["at_ms"] <= time)
                frame = frame_at(data, state["clip"], time - state["clip_started_ms"])
                px, py = frame["pivot"]
                position = state["position"]
                origin = (round(position[0] - px), round(position[1] - py))
                sort_y = position[1] - py + frame["sort_origin"][1]
                posed.append((sort_y, actor["id"], {**actor, "clip": state["clip"]}, frame, image, origin))
            posed.sort(key=lambda value: (value[0], value[1]))
            actor_trace = []
            regions = []
            for sort_y, actor_id, actor, frame, image, origin in posed:
                x, y, w, h = frame["rect"]
                canvas.alpha_composite(image.crop((x, y, x + w, y + h)), origin)
                for region in world_regions(frame, origin):
                    regions.append({**region, "actor": actor_id})
                actor_trace.append({"actor": actor_id, "frame": frame["id"], "clip": actor["clip"],
                                    "origin": list(origin), "sort_y": sort_y})
            overlaps = []
            for i, first in enumerate(regions):
                for second in regions[i+1:]:
                    if first["actor"] != second["actor"] and overlap(first["polygon"], second["polygon"]):
                        overlaps.append({"first": {key: first[key] for key in ("actor", "id", "role")},
                                         "second": {key: second[key] for key in ("actor", "id", "role")}})
            if scene.get("debug_regions", False):
                draw = ImageDraw.Draw(canvas)
                for region in regions:
                    draw.polygon([tuple(point) for point in region["polygon"]], outline="#ff44dd")
            filename = f"scene_{index:04d}.png"
            canvas.save(bundle / filename)
            trace.append({"time_ms": time, "image": filename, "actors": actor_trace,
                          "regions": regions, "region_overlaps": overlaps})
        report = {"schema_version": 1, "status": "rendered", "trace": trace,
                  "verification_scope": "exported playback, pivot placement, stable Y sorting and declared convex-region overlap",
                  "unverified": ["collision behavior", "transition blending", "artistic quality", "tile seams", "engine integration"]}
        (bundle / "trace.json").write_text(json.dumps(report, indent=2))
        bundle.rename(destination)
    return {**report, "output": str(destination)}


def register(sub):
    parser = sub.add_parser("scene", help="Render a reference scene from exported manifests, preserving pivots and Y sorting.")
    parser.add_argument("source")
    parser.add_argument("--output", required=True)
    parser.add_argument("--json", action="store_true")

    def run(args):
        print(json.dumps(render_scene(args.source, args.output)))
        return 0

    parser.set_defaults(func=run)

"""Build artifact-bound visual inputs without author or peer-review arguments."""

import hashlib
import io
import json
from copy import deepcopy
from pathlib import Path

from PIL import Image, ImageSequence

from pixelai.evidence import verify_evidence
from pixelai.manifest import load_manifest


def prepare_packet(project, contract, construction, role):
    """Generate native and integer-zoom frames for an isolated reviewer.

    The host still must establish context isolation and record observations.
    Creating this packet alone is not evidence that anyone viewed it.
    """
    root = Path(project).resolve()
    records = verify_evidence(root, construction["evidence"])
    image_record = next(record for record in records if record["path"] == construction["image_path"])
    image_path = root / image_record["path"]
    manifest_name = construction.get("manifest_path")
    if manifest_name:
        manifest, texture = load_manifest(root / manifest_name)
        frames = []
        for record in manifest["frames"]:
            x, y, width, height = record["rect"]
            frames.append((record["id"], texture.crop((x, y, x + width, y + height))))
    else:
        manifest = None
        with Image.open(image_path) as source:
            frames = [(str(index), frame.convert("RGBA")) for index, frame in enumerate(ImageSequence.Iterator(source))]
    motion = {"status": "unavailable", "reason": "No construction source supplied"}
    if construction.get("source_path"):
        from pixelai.provenance import verify_construction
        motion = verify_construction(root, construction, contract.get("native_size"))["motion_diagnostics"]
    review_contract = {key: contract.get(key) for key in ("category", "native_size", "art_direction", "functional_requirements", "delivery")}
    identity = hashlib.sha256(json.dumps({"protocol": 2, "role": role, "artifact": image_record,
                                          "manifest": manifest, "contract": review_contract, "motion": motion}, sort_keys=True).encode()).hexdigest()
    directory = root / ".pixelai" / "review_frames" / identity
    if not directory.resolve().is_relative_to(root):
        raise ValueError("Review frame directory must remain inside the project")
    directory.mkdir(parents=True, exist_ok=True)
    views = []
    for index, (frame_id, image) in enumerate(frames):
        for zoom in (1, 4):
            view = image if zoom == 1 else image.resize((image.width * zoom, image.height * zoom), Image.Resampling.NEAREST)
            buffer = io.BytesIO()
            view.save(buffer, format="PNG")
            payload = buffer.getvalue()
            path = directory / f"frame_{index:04d}_{zoom}x.png"
            if not path.resolve().is_relative_to(root):
                raise ValueError("Review view must remain inside the project")
            if path.exists():
                if path.read_bytes() != payload:
                    raise ValueError("Review view integrity failure")
            else:
                with path.open("xb") as output:
                    output.write(payload)
            views.append({"frame": frame_id, "zoom": zoom, "path": path.relative_to(root).as_posix(),
                          "sha256": hashlib.sha256(payload).hexdigest()})
    timing = {}
    neutral_manifest = deepcopy(manifest)
    if neutral_manifest is not None:
        from pixelai.animation_score import score_beats
        records = {frame["id"]: frame for frame in manifest["frames"]}
        for name, clip in neutral_manifest["clips"].items():
            timing[name] = {"beats": score_beats(clip, records), "events": deepcopy(clip.get("score", {}).get("events", []))}
            clip.pop("score", None)
    return {"schema_version": 1, "packet_id": identity, "role": role,
            "category": contract.get("category"), "art_direction": contract.get("art_direction"),
            "functional_requirements": contract.get("functional_requirements", []),
            "delivery": contract.get("delivery", {}),
            "artifact": image_record, "views": views,
            "runtime_manifest": neutral_manifest if role == "context_review" else None,
            "animation_timing": timing if role == "context_review" else {},
            "motion_diagnostics": motion,
            "observation_status": "not_attested",
            "host_requirements": ["Use a context separate from the author and the other reviewer", "Inspect every native and zoomed frame", "Do not import author justifications or another review's scores"]}

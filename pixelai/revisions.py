"""Repair-aware revision identity independent of filenames and author claims."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageSequence

from pixelai.quality import artifact_identity


def contract_identity(contract):
    fields = {key: contract.get(key) for key in ("category", "native_size", "art_direction", "functional_requirements", "delivery")}
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()


def construction_identity(project, construction):
    root = Path(project)
    path = root / construction["image_path"]
    identity, _ = artifact_identity(path)
    runtime = None
    if construction.get("manifest_path"):
        data = json.loads((root / construction["manifest_path"]).read_text(encoding="utf-8-sig"))
        runtime = {"frames": [{key: frame.get(key) for key in ("rect", "duration_ms", "pivot", "ground_anchor", "sort_origin", "regions", "sockets", "view", "action", "state")}
                              for frame in data["frames"]], "clips": data["clips"], "transitions": data.get("transitions", [])}
    elif path.suffix.lower() == ".gif":
        with Image.open(path) as image:
            runtime = {"loop": image.info.get("loop"), "durations_ms": [frame.info.get("duration") for frame in ImageSequence.Iterator(image)]}
    encoded = json.dumps({"content": identity["content_sha256"], "runtime": runtime}, sort_keys=True).encode()
    return {"content_sha256": identity["content_sha256"], "revision_sha256": hashlib.sha256(encoded).hexdigest()}


def check_rejected_revision(candidate, rejections):
    for rejection in rejections:
        previous = rejection["identity"]
        if previous["revision_sha256"] == candidate["revision_sha256"]:
            raise ValueError("Unchanged rejected construction cannot be resubmitted for another review")
        artistic = set(rejection["defects"]) - {"technical_integrity", "game_readiness"}
        if artistic and previous["content_sha256"] == candidate["content_sha256"]:
            raise ValueError("Artistic rejection requires changed pixels; metadata-only changes cannot resolve it")

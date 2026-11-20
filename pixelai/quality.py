"""Evidence-bound commercial review; numerical checks never approve artwork."""

import hashlib
import json
from pathlib import Path

from pixelai.inspect_tool import analyze_canvas, load_frames_as_canvases


CRITERIA = {
    "professional_quality": "Compare finish against a named professional reference; explain remaining weaknesses.",
    "readability": "Identify each subject at native resolution from silhouette and proportions.",
    "pixel_clustering": "Inspect clusters for noise, isolated pixels, banding and accidental geometry.",
    "color_and_lighting": "Check palette harmony, volume, light direction and controlled contrast.",
    "materials": "Explain how each material reads through its structure rather than generic pattern noise.",
    "specialized_design": "Check anatomy, architecture and characteristic features of the subject.",
    "artistic_detail": "Assess depth, personality and finish beyond a merely acceptable primitive.",
    "originality": "Compare with prior and rejected work; explain new geometry and legitimate reuse.",
    "consistency": "Compare scale, perspective, style and detail density within the intended catalog.",
    "technical_integrity": "Verify dimensions, transparency, borders, directions and absence of deformation.",
    "game_readiness": "Verify complete views/states/animations and integration without manual repair.",
}


def artifact_identity(path):
    """Ignore metadata for duplicate detection, but bind review to exact file bytes."""
    path = Path(path)
    frames = load_frames_as_canvases(path)
    pixels = hashlib.sha256()
    shape = hashlib.sha256()
    content = hashlib.sha256()
    for frame in frames:
        dimensions = f"{frame.width}x{frame.height}:".encode()
        pixels.update(dimensions)
        shape.update(dimensions)
        for color in frame.pixels:
            pixels.update(bytes(color if color[3] else (0, 0, 0, 0)))
            shape.update(bytes([int(color[3] > 0)]))
        occupied = [(i % frame.width, i // frame.width) for i, p in enumerate(frame.pixels) if p[3]]
        if occupied:
            left, top = min(x for x, _ in occupied), min(y for _, y in occupied)
            right, bottom = max(x for x, _ in occupied), max(y for _, y in occupied)
            content.update(f"{right-left+1}x{bottom-top+1}:".encode())
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    p = frame.get_pixel(x, y)
                    content.update(bytes(p if p[3] else (0, 0, 0, 0)))
        else:
            content.update(b"empty:")
    return {"file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "pixel_sha256": pixels.hexdigest(), "content_sha256": content.hexdigest(),
            "silhouette_sha256": shape.hexdigest()}, frames


def review_template(path):
    identity, frames = artifact_identity(path)
    return {
        "schema_version": 1, "artifact": identity,
        "generated_by": "", "reviewed_by": "",
        "comparison_reference": {"name": "", "url": "", "notes": ""},
        "inspection": {"native_resolution": False, "integer_zoom": 0},
        "contract": {"width": frames[0].width, "height": frames[0].height,
                     "frame_count": len(frames), "minimum_margin": 1,
                     "max_colors": 32, "max_islands": 1,
                     "required_views": [], "views": []},
        "criteria": {key: {"decision": "unverified", "evidence": "", "guidance": guidance}
                     for key, guidance in CRITERIA.items()},
    }


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _technical_checks(frames, stats, contract):
    """Validate explicit delivery requirements and per-view content, not aesthetics."""
    failures = []
    for name in ("width", "height", "frame_count", "minimum_margin", "max_colors", "max_islands"):
        if name not in contract:
            raise ValueError(f"contract missing {name}")
        _integer(contract[name], f"contract.{name}", 0 if name == "minimum_margin" else 1)
    if len(frames) != contract["frame_count"]:
        failures.append("Frame count differs from delivery contract")
    for index, (frame, summary) in enumerate(zip(frames, stats)):
        if (frame.width, frame.height) != (contract["width"], contract["height"]):
            failures.append(f"frame[{index}] dimensions differ from delivery contract")
        if not summary["opaque_pixels"]:
            failures.append(f"frame[{index}] is empty")
        if min(summary["margins"].values()) < contract["minimum_margin"]:
            failures.append(f"frame[{index}] violates minimum margin")
        if summary["unique_colors"] > contract["max_colors"]:
            failures.append(f"frame[{index}] exceeds color budget")
        if summary["islands"] > contract["max_islands"]:
            failures.append(f"frame[{index}] exceeds island budget")

    required = contract.get("required_views", [])
    views = contract.get("views", [])
    if not isinstance(required, list) or not all(isinstance(v, str) and v for v in required):
        raise ValueError("contract.required_views must be an array of nonempty names")
    if len(set(required)) != len(required) or not isinstance(views, list):
        raise ValueError("contract required view names must be unique and views must be an array")
    groups = {}
    for view in views:
        if not isinstance(view, dict):
            raise ValueError("contract.views entries must be objects")
        name, group = view.get("name"), view.get("group", "default")
        if not isinstance(name, str) or not name or not isinstance(group, str) or not group:
            raise ValueError("view name/group must be nonempty strings")
        frame_index = _integer(view.get("frame", 0), "view.frame")
        x, y = (_integer(view.get(k), f"view.{k}") for k in ("x", "y"))
        w, h = (_integer(view.get(k), f"view.{k}", 1) for k in ("w", "h"))
        if frame_index >= len(frames):
            raise ValueError("view.frame is outside the image")
        frame = frames[frame_index]
        if x + w > frame.width or y + h > frame.height:
            raise ValueError("view rectangle is outside the image")
        content = tuple(frame.get_pixel(px, py) for py in range(y, y + h) for px in range(x, x + w))
        group_views = groups.setdefault(group, {})
        if name in group_views:
            raise ValueError(f"duplicate view {group}/{name}")
        group_views[name] = (w, h, content)
        if not any(p[3] for p in content):
            failures.append(f"view {group}/{name} is empty")
    if required and not groups:
        failures.append("Required views have no rectangles to inspect")
    for group, group_views in groups.items():
        missing = set(required) - group_views.keys()
        if missing:
            failures.append(f"{group} missing views: {', '.join(sorted(missing))}")
        contents = [group_views[name] for name in required if name in group_views]
        if len({(w, h) for w, h, _ in contents}) > 1:
            failures.append(f"{group} views have inconsistent dimensions")
        if len(set(contents)) != len(contents):
            failures.append(f"{group} required views contain identical images")
    return failures


def assess_artifact(path, review=None, catalog=None):
    """Fail closed: approval requires every criterion and an independent attestation."""
    identity, frames = artifact_identity(path)
    stats = [analyze_canvas(frame) for frame in frames]
    failures, pending, warnings = [], [], []
    if not any(s["opaque_pixels"] for s in stats):
        failures.append("Artifact is empty")
    entries = (catalog or {}).get("entries", [])
    if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
        raise ValueError("catalog.entries must be an array of objects")
    for entry in entries:
        same_pixels = entry.get("pixel_sha256") == identity["pixel_sha256"]
        same_content = entry.get("content_sha256") == identity["content_sha256"]
        if entry.get("status") == "rejected" and (same_pixels or same_content):
            failures.append("Exact artwork was previously rejected (metadata/filename changes do not make it new)")
        elif entry.get("silhouette_sha256") == identity["silhouette_sha256"]:
            warnings.append(f"Existing silhouette matches catalog entry {entry.get('path', '?')}; review originality")
    if review is None:
        pending.extend(CRITERIA)
    else:
        if not isinstance(review, dict) or review.get("schema_version") != 1:
            raise ValueError("review must be a schema_version 1 object")
        if review.get("artifact") != identity:
            failures.append("Review is stale or belongs to a different artifact")
        generator, reviewer = review.get("generated_by"), review.get("reviewed_by")
        if not isinstance(generator, str) or not generator.strip() or not isinstance(reviewer, str) or not reviewer.strip():
            pending.append("generator and reviewer identities")
        elif generator.strip().casefold() == reviewer.strip().casefold():
            failures.append("Generator cannot approve its own artwork")
        reference = review.get("comparison_reference", {})
        if not isinstance(reference, dict):
            raise ValueError("comparison_reference must be an object")
        if not all(isinstance(reference.get(key), str) and reference[key].strip()
                   for key in ("name", "url", "notes")):
            pending.append("named professional comparison reference")
        elif not reference["url"].startswith(("https://", "http://")):
            failures.append("comparison_reference.url must be an HTTP(S) source")
        inspection = review.get("inspection", {})
        if not isinstance(inspection, dict) or inspection.get("native_resolution") is not True:
            pending.append("inspection at native resolution")
        zoom = inspection.get("integer_zoom") if isinstance(inspection, dict) else None
        if type(zoom) is not int or zoom < 2:
            pending.append("inspection at integer zoom >= 2")
        contract = review.get("contract")
        if not isinstance(contract, dict):
            pending.append("explicit delivery contract")
        else:
            failures.extend(_technical_checks(frames, stats, contract))
        criteria = review.get("criteria", {})
        if not isinstance(criteria, dict):
            raise ValueError("review.criteria must be an object")
        for key in CRITERIA:
            entry = criteria.get(key, {})
            if not isinstance(entry, dict):
                raise ValueError(f"review.criteria.{key} must be an object")
            decision, evidence = entry.get("decision", "unverified"), entry.get("evidence", "")
            if decision not in ("pass", "fail", "unverified"):
                raise ValueError(f"review.criteria.{key}.decision must be pass, fail or unverified")
            if decision == "fail":
                failures.append(f"{key}: {evidence or 'reviewer rejected'}")
            elif decision != "pass" or not isinstance(evidence, str) or len(evidence.strip()) < 20:
                pending.append(key)
    for index, summary in enumerate(stats):
        if summary["isolated_single_pixels"]:
            warnings.append(f"frame[{index}] has isolated pixels; inspect intended particles versus noise")
    status = "rejected" if failures else ("needs_review" if pending else "approved")
    return {"schema_version": 1, "status": status, "commercial_ready": status == "approved",
            "approval_basis": "independent reviewer attestation plus technical contract; not an automatic aesthetic judgment",
            "artifact": identity, "frames": stats, "failures": failures,
            "pending": pending, "warnings": warnings}


def record_assessment(path, image, assessment):
    """Persist rejection/approval identity without replacing a previous rejection."""
    path = Path(path)
    catalog = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {"schema_version": 1, "entries": []}
    if not isinstance(catalog, dict) or not isinstance(catalog.get("entries"), list):
        raise ValueError("catalog must contain entries array")
    catalog["entries"].append({"path": str(Path(image).resolve()), "status": assessment["status"],
                               **assessment["artifact"], "failures": assessment["failures"]})
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)

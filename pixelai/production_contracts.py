"""Stage-specific requirements for managed agent submissions.

These checks establish completeness and traceability, not artistic quality or
trusted host isolation. Approval remains unavailable without those adapters.
"""

import json
from pathlib import Path

from PIL import Image, ImageSequence

from pixelai.quality import CRITERIA
from pixelai.provenance import verify_construction
from pixelai.diversity import compare_silhouettes


CATEGORIES = ("human", "creature", "vegetation", "building", "rock", "item",
              "material", "tile", "ui", "portrait", "background", "illustration", "vfx")

REQUIREMENTS = {
    "contract": ["category", "native_size", "art_direction", "functional_requirements"],
    "alternatives": ["proposals (six distinct descriptions with source_path and image_path evidence)", "selected_id"],
    "construction": ["source_path", "image_path", "source evidence", "matching PNG or GIF evidence", "manifest_path for atlas PNGs"],
    "art_review": ["context_id", "author_context_id", "criteria", "native_resolution", "integer_zoom"],
    "context_review": ["context_id", "author_context_id", "criteria", "native_resolution", "integer_zoom"],
    "verification": ["runtime evidence (not yet sufficient for approval)"],
}


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def validate_submission(stage, data, previous, project=None):
    """Reject missing stage output and conflicting declared review identities."""
    if project is not None and stage in ("construction", "art_review", "context_review"):
        images = []
        sources = []
        for record in data["evidence"]:
            path = Path(project) / record["path"]
            if path.suffix.lower() in (".png", ".gif", ".webp"):
                with Image.open(path) as image:
                    if not any(frame.convert("RGBA").getchannel("A").getbbox() for frame in ImageSequence.Iterator(image)):
                        raise ValueError("Image evidence cannot be empty")
                    images.append(record)
            elif path.suffix.lower() == ".json":
                source = json.loads(path.read_text())
                if isinstance(source, dict) and "width" in source and "height" in source:
                    sources.append(record)
        if not images:
            raise ValueError("Construction and visual review require actual image evidence")
        if stage == "construction" and not sources:
            raise ValueError("Construction requires JSON source spec evidence")
        if stage == "construction":
            verify_construction(project, data, previous.get("contract", {}).get("native_size"))
    if stage == "contract":
        if data.get("category") not in CATEGORIES:
            raise ValueError(f"category must be one of {', '.join(CATEGORIES)}")
        size = data.get("native_size")
        if not isinstance(size, list) or len(size) != 2 or any(type(v) is not int or v < 1 for v in size):
            raise ValueError("native_size requires two positive integers")
        _text(data.get("art_direction"), "art_direction")
        requirements = data.get("functional_requirements")
        if not isinstance(requirements, list) or any(not isinstance(r, str) or not r.strip() for r in requirements):
            raise ValueError("functional_requirements must be an array of nonempty strings")
    elif stage == "alternatives":
        proposals = data.get("proposals")
        if not isinstance(proposals, list) or len(proposals) != 6:
            raise ValueError("Exactly six structural proposals are required")
        ids, structures = set(), set()
        for proposal in proposals:
            if not isinstance(proposal, dict):
                raise ValueError("Proposals must be objects")
            _text(proposal.get("id"), "proposal.id")
            _text(proposal.get("structure"), "proposal.structure")
            ids.add(proposal["id"])
            structures.add(" ".join(proposal["structure"].casefold().split()))
        if len(ids) != 6 or len(structures) != 6:
            raise ValueError("Proposal ids and structural descriptions must be distinct")
        if data.get("selected_id") not in ids:
            raise ValueError("selected_id must identify one of the proposals")
        if project is not None:
            images = []
            contents = set()
            for proposal in proposals:
                if not isinstance(proposal.get("image_path"), str) or Path(proposal["image_path"]).suffix.lower() != ".png":
                    raise ValueError("Each proposal requires native PNG image_path evidence")
                verify_construction(project, {**proposal, "evidence": data["evidence"]}, previous.get("contract", {}).get("native_size"))
                path = Path(project) / proposal["image_path"]
                with Image.open(path) as image:
                    image = image.convert("RGBA")
                    if not image.getchannel("A").getbbox():
                        raise ValueError("Proposal images cannot be empty")
                    getter = getattr(image, "get_flattened_data", image.getdata)
                    signature = image.size, tuple(pixel if pixel[3] else (0, 0, 0, 0) for pixel in getter())
                    if signature in contents:
                        raise ValueError("Structural proposals cannot repeat identical rendered images")
                    contents.add(signature)
                images.append((proposal["id"], path))
            data["proposal_comparisons"] = [
                {"first": first_id, "second": second_id, **compare_silhouettes(first_path, second_path)}
                for index, (first_id, first_path) in enumerate(images)
                for second_id, second_path in images[index+1:]
            ]
    elif stage in ("art_review", "context_review"):
        construction = previous.get("construction")
        if construction:
            rendered_path = construction["image_path"]
            expected = next(r for r in construction["evidence"] if r["path"] == rendered_path)
            if expected not in data["evidence"]:
                raise ValueError("Review must include the exact constructed artifact evidence")
        context, author = data.get("context_id"), data.get("author_context_id")
        _text(context, "context_id")
        _text(author, "author_context_id")
        if context.strip().casefold() == author.strip().casefold():
            raise ValueError("Review must declare a different context from the author")
        other = previous.get("art_review") if stage == "context_review" else None
        if other and (context.strip().casefold() == other["context_id"].strip().casefold() or author != other["author_context_id"]):
            raise ValueError("Context reviewers must be separate and agree on the author identity")
        if data.get("native_resolution") is not True or type(data.get("integer_zoom")) is not int or data["integer_zoom"] < 2:
            raise ValueError("Review requires native inspection and integer zoom >= 2")
        criteria = data.get("criteria")
        if not isinstance(criteria, dict) or set(criteria) != set(CRITERIA):
            raise ValueError("Review must address all eleven quality criteria")
        for name, result in criteria.items():
            if not isinstance(result, dict) or type(result.get("score")) is not int or not 0 <= result["score"] <= 4:
                raise ValueError(f"{name} requires an integer score from 0 to 4")
            _text(result.get("observation"), f"{name}.observation")
            if not isinstance(result.get("evidence_indices"), list) or not result["evidence_indices"]:
                raise ValueError(f"{name} must reference evidence indices")
            for index in result["evidence_indices"]:
                if type(index) is not int or not 0 <= index < len(data["evidence"]):
                    raise ValueError(f"{name} references missing evidence")

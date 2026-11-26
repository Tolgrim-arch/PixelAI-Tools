"""Content-bound evidence records for managed production tasks."""

import hashlib
from pathlib import Path


def bind_evidence(project, records):
    """Validate project-local files and freeze their content identity."""
    if not isinstance(records, list) or not records:
        raise ValueError("Evidence must be a nonempty array of file records")
    root = Path(project).resolve()
    bound = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ValueError("Each evidence record requires a project-relative path")
        source = Path(record["path"])
        if source.is_absolute():
            raise ValueError("Evidence paths must be project-relative")
        path = (root / source).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("Evidence must resolve to an existing file inside the project")
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if record.get("sha256", digest) != digest:
            raise ValueError(f"Stale evidence: {source}")
        archive = root / ".pixelai" / "artifacts"
        if not archive.resolve().is_relative_to(root):
            raise ValueError("Evidence archive must remain inside the project")
        archive.mkdir(parents=True, exist_ok=True)
        snapshot = archive / digest
        try:
            with snapshot.open("xb") as target:
                target.write(payload)
        except FileExistsError:
            if hashlib.sha256(snapshot.read_bytes()).hexdigest() != digest:
                raise ValueError("Archived evidence integrity failure")
        bound.append({"path": path.relative_to(root).as_posix(), "sha256": digest})
    return bound


def verify_evidence(project, records):
    return bind_evidence(project, records)

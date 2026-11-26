"""Persistent, fail-closed agent task queue. No review attestation implies approval."""

import json
import sqlite3
from pathlib import Path

from pixelai.evidence import bind_evidence, verify_evidence


STAGES = (
    ("contract", "Define category, native dimensions, art direction, functional requirements and budget."),
    ("alternatives", "Compare six structural proposals as silhouettes; explain meaningful differences, not recolors."),
    ("construction", "Build the selected proposal and supply source specs and rendered artifacts."),
    ("art_review", "Request a separate visual context: inspect native pixels, integer zoom, anatomy, materials, personality and catalog repetition."),
    ("context_review", "Request another context: verify pivots, collisions, sorting, directions, transitions, backgrounds, relative scale, gameplay states and tile seams where applicable."),
    ("verification", "Provide machine-verifiable runtime evidence and artifact-bound reviews. This initial implementation cannot certify release."),
)


def connect(project):
    root = Path(project).resolve()
    if not (root / "brief.json").is_file():
        raise ValueError("Project must contain brief.json; use project init first")
    db = sqlite3.connect(root / "workflow.sqlite3")
    db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, stage TEXT UNIQUE, guidance TEXT, response TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, task_id INTEGER, payload TEXT NOT NULL)")
    return db


def initialize(project, brief):
    data = json.loads(Path(brief).read_text())
    if not isinstance(data, dict) or not isinstance(data.get("goal"), str) or not data["goal"].strip():
        raise ValueError("Brief requires a nonempty goal")
    root = Path(project).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with (root / "brief.json").open("x") as out:
        json.dump(data, out, indent=2)
    return {"project": str(root), "status": "initialized"}


def operate(project, action, task=None, response=None):
    db = connect(project)
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            if action == "start":
                db.executemany("INSERT OR IGNORE INTO tasks(stage,guidance) VALUES (?,?)", STAGES)
            if action == "submit":
                current = db.execute("SELECT id FROM tasks WHERE response IS NULL ORDER BY id LIMIT 1").fetchone()
                if current is None or current[0] != task:
                    raise ValueError("Only the current pending task may be submitted")
                data = json.loads(Path(response).read_text())
                if not isinstance(data, dict) or not isinstance(data.get("evidence"), list) or not data["evidence"]:
                    raise ValueError("Response requires a nonempty evidence array")
                data["evidence"] = bind_evidence(project, data["evidence"])
                db.execute("UPDATE tasks SET response=? WHERE id=?", (json.dumps(data), task))
                db.execute("INSERT INTO events(task_id,payload) VALUES (?,?)", (task, json.dumps(data)))
            for completed_id, payload in db.execute("SELECT id,response FROM tasks WHERE response IS NOT NULL ORDER BY id"):
                try:
                    verify_evidence(project, json.loads(payload)["evidence"])
                except (ValueError, OSError, KeyError, TypeError):
                    db.execute("UPDATE tasks SET response=NULL WHERE id>=?", (completed_id,))
                    db.execute("INSERT INTO events(task_id,payload) VALUES (?,?)", (completed_id, json.dumps({"event": "evidence_invalidated"})))
                    break
            row = db.execute("SELECT id,stage,guidance FROM tasks WHERE response IS NULL ORDER BY id LIMIT 1").fetchone()
            if row:
                return {"status": "needs_agent", "task_id": row[0], "stage": row[1], "guidance": row[2], "approval_supported": False}
            count = db.execute("SELECT count(*) FROM tasks").fetchone()[0]
            return {"status": "blocked", "reason": "Artifact verification and host review adapters are not implemented" if count else "Start the workflow first", "approval_supported": False}
    finally:
        db.close()


def register(sub):
    def emit(value):
        print(json.dumps(value))
        return 0

    project = sub.add_parser("project", help="Initialize a managed art project.")
    ps = project.add_subparsers(dest="project_action", required=True)
    init = ps.add_parser("init", help="Create a project from a JSON brief containing goal.")
    init.add_argument("directory")
    init.add_argument("--brief", required=True)
    init.set_defaults(func=lambda a: emit(initialize(a.directory, a.brief)))
    workflow = sub.add_parser("workflow", help="Run the persistent experimental agent task queue; approval is not yet supported.")
    ws = workflow.add_subparsers(dest="workflow_action", required=True)
    for action in ("start", "next", "status", "resume", "submit"):
        parser = ws.add_parser(action, help=f"{action.capitalize()} a managed workflow.")
        parser.add_argument("project")
        parser.add_argument("--json", action="store_true")
        if action == "submit":
            parser.add_argument("--task", type=int, required=True)
            parser.add_argument("--input", required=True)
        parser.set_defaults(func=lambda a: emit(operate(a.project, a.workflow_action, getattr(a, "task", None), getattr(a, "input", None))))

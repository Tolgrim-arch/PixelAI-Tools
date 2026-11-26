"""Persistent, fail-closed agent task queue. No review attestation implies approval."""

import json
import hashlib
import sqlite3
from pathlib import Path

from pixelai.evidence import bind_evidence, verify_evidence
from pixelai.production_contracts import REQUIREMENTS, validate_submission
from pixelai.production_guidance import task_guidance


STAGES = (
    ("contract", "Define category, native dimensions, art direction, functional requirements and budget."),
    ("alternatives", "Compare six structural proposals as silhouettes; explain meaningful differences, not recolors."),
    ("construction", "Build the selected proposal and supply source specs and rendered artifacts."),
    ("art_review", "Request a separate visual context: inspect native pixels, integer zoom, anatomy, materials, personality and catalog repetition."),
    ("context_review", "Request another context: verify pivots, collisions, sorting, directions, transitions, backgrounds, relative scale, gameplay states and tile seams where applicable."),
    ("verification", "Provide machine-verifiable runtime evidence and artifact-bound reviews. This initial implementation cannot certify release."),
)

DEFAULT_BUDGETS = {"rendered_revisions": 36, "visual_reviews": 24}


def _budgets(project):
    brief = json.loads((Path(project) / "brief.json").read_text())
    configured = brief.get("budgets", {})
    if not isinstance(configured, dict) or set(configured) - DEFAULT_BUDGETS.keys():
        raise ValueError("budgets accepts rendered_revisions and visual_reviews only")
    limits = {**DEFAULT_BUDGETS, **configured}
    if any(type(value) is not int or value < 1 for value in limits.values()):
        raise ValueError("Budgets must be positive integers")
    return limits


def _usage(db):
    counts = dict(db.execute("SELECT t.stage,count(*) FROM events e JOIN tasks t ON t.id=e.task_id WHERE json_extract(e.payload,'$.evidence') IS NOT NULL GROUP BY t.stage"))
    return {"rendered_revisions": counts.get("construction", 0),
            "visual_reviews": counts.get("art_review", 0) + counts.get("context_review", 0)}


def _invalidate_stale(db, project):
    for completed_id, payload in db.execute("SELECT id,response FROM tasks WHERE response IS NOT NULL ORDER BY id").fetchall():
        try:
            verify_evidence(project, json.loads(payload)["evidence"])
        except (ValueError, OSError, KeyError, TypeError):
            db.execute("UPDATE tasks SET response=NULL WHERE id>=?", (completed_id,))
            db.execute("INSERT INTO events(task_id,payload) VALUES (?,?)", (completed_id, json.dumps({"event": "evidence_invalidated"})))
            break


def connect(project):
    root = Path(project).resolve()
    if not (root / "brief.json").is_file():
        raise ValueError("Project must contain brief.json; use project init first")
    db = sqlite3.connect(root / "workflow.sqlite3")
    db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, stage TEXT UNIQUE, guidance TEXT, response TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, task_id INTEGER, payload TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
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
            limits = _budgets(project)
            brief_hash = hashlib.sha256((Path(project) / "brief.json").read_bytes()).hexdigest()
            old_brief = db.execute("SELECT value FROM settings WHERE key='brief_sha256'").fetchone()
            if old_brief and old_brief[0] != brief_hash:
                db.execute("UPDATE tasks SET response=NULL")
                db.execute("INSERT INTO events(payload) VALUES (?)", (json.dumps({"event": "brief_changed", "previous": old_brief[0], "current": brief_hash}),))
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES ('brief_sha256',?)", (brief_hash,))
            _invalidate_stale(db, project)
            if action == "start":
                db.executemany("INSERT OR IGNORE INTO tasks(stage,guidance) VALUES (?,?)", STAGES)
            if action == "submit":
                current = db.execute("SELECT id,stage FROM tasks WHERE response IS NULL ORDER BY id LIMIT 1").fetchone()
                if current is None or current[0] != task:
                    raise ValueError("Only the current pending task may be submitted")
                budget_key = "visual_reviews" if current[1] in ("art_review", "context_review") else "rendered_revisions" if current[1] == "construction" else None
                if budget_key and _usage(db)[budget_key] >= limits[budget_key]:
                    raise ValueError(f"Budget exhausted: {budget_key}")
                data = json.loads(Path(response).read_text())
                if not isinstance(data, dict) or not isinstance(data.get("evidence"), list) or not data["evidence"]:
                    raise ValueError("Response requires a nonempty evidence array")
                data["evidence"] = bind_evidence(project, data["evidence"])
                previous = {stage: json.loads(payload) for stage, payload in db.execute("SELECT stage,response FROM tasks WHERE response IS NOT NULL")}
                validate_submission(current[1], data, previous, project)
                db.execute("UPDATE tasks SET response=? WHERE id=?", (json.dumps(data), task))
                db.execute("INSERT INTO events(task_id,payload) VALUES (?,?)", (task, json.dumps(data)))
                if current[1] in ("art_review", "context_review"):
                    defects = {name: result for name, result in data["criteria"].items() if result["score"] < 3}
                    if defects:
                        construction = db.execute("SELECT id FROM tasks WHERE stage='construction'").fetchone()[0]
                        db.execute("UPDATE tasks SET response=NULL WHERE id>=?", (construction,))
                        db.execute("INSERT INTO events(task_id,payload) VALUES (?,?)", (construction, json.dumps({"event": "repair_required", "defects": defects})))
                        recent = db.execute("SELECT payload FROM events WHERE json_extract(payload,'$.event')='repair_required' ORDER BY id DESC LIMIT 3").fetchall()
                        if len(recent) == 3 and len({tuple(sorted(json.loads(item[0])["defects"])) for item in recent}) == 1:
                            alternatives = db.execute("SELECT id FROM tasks WHERE stage='alternatives'").fetchone()[0]
                            db.execute("UPDATE tasks SET response=NULL WHERE id>=?", (alternatives,))
                            db.execute("INSERT INTO events(task_id,payload) VALUES (?,?)", (alternatives, json.dumps({"event": "strategy_change_required", "reason": "Three reviews repeat the same failing criteria"})))
            row = db.execute("SELECT id,stage,guidance FROM tasks WHERE response IS NULL ORDER BY id LIMIT 1").fetchone()
            if row:
                usage = _usage(db)
                repair = db.execute("SELECT payload FROM events WHERE json_extract(payload,'$.event')='repair_required' ORDER BY id DESC LIMIT 1").fetchone()
                key = "visual_reviews" if row[1] in ("art_review", "context_review") else "rendered_revisions" if row[1] == "construction" else None
                if key and usage[key] >= limits[key]:
                    return {"status": "blocked", "reason": f"Budget exhausted: {key}", "usage": usage, "limits": limits,
                            "latest_repair": json.loads(repair[0]) if repair else None, "approval_supported": False}
                contract = db.execute("SELECT response FROM tasks WHERE stage='contract'").fetchone()
                category = json.loads(contract[0]).get("category") if contract and contract[0] else None
                return {"status": "needs_agent", "task_id": row[0], "stage": row[1], "guidance": row[2],
                        "required_output": REQUIREMENTS[row[1]], "usage": usage, "limits": limits,
                        "quality_protocol": task_guidance(category, row[1]),
                        "latest_repair": json.loads(repair[0]) if repair else None, "approval_supported": False}
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

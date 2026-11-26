"""Persistent task ordering and fail-closed behavior."""
import json
from pathlib import Path
import tempfile
import unittest

from pixelai.workflow import initialize, operate


class WorkflowTest(unittest.TestCase):
    def test_resume_order_and_no_attestation_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "input.json"
            brief.write_text(json.dumps({"goal": "Create a readable potion"}))
            project = root / "project"
            initialize(project, brief)
            first = operate(project, "start")
            self.assertEqual(first, operate(project, "start"))
            self.assertEqual(first, operate(project, "resume"))
            response = root / "response.json"
            evidence = project / "evidence.txt"
            evidence.write_text("Synthetic evidence; not artistic approval")
            response.write_text(json.dumps({"evidence": [{"path": "evidence.txt"}]}))
            with self.assertRaises(ValueError):
                operate(project, "submit", 99, response)
            for _ in range(6):
                task = operate(project, "next")
                operate(project, "submit", task["task_id"], response)
            final = operate(project, "status")
            self.assertEqual(final["status"], "blocked")
            self.assertFalse(final["approval_supported"])
            evidence.write_text("Changed evidence")
            self.assertEqual(operate(project, "resume")["stage"], "contract")

    def test_missing_and_outside_evidence_cannot_advance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "brief.json"
            brief.write_text(json.dumps({"goal": "Test"}))
            project = root / "project"
            initialize(project, brief)
            first = operate(project, "start")
            response = root / "response.json"
            for record in ("Claim only", {"path": "missing.png"}, {"path": "../brief.json"}):
                response.write_text(json.dumps({"evidence": [record]}))
                with self.assertRaises(ValueError):
                    operate(project, "submit", first["task_id"], response)
                self.assertEqual(operate(project, "next")["task_id"], first["task_id"])

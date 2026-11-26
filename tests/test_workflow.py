"""Persistent task ordering and fail-closed behavior."""
import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.workflow import initialize, operate
from pixelai.quality import CRITERIA


class WorkflowTest(unittest.TestCase):
    def test_three_repeated_rejections_require_new_alternatives(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "brief.json"
            brief.write_text(json.dumps({"goal": "Test strategy changes"}))
            project = root / "project"
            initialize(project, brief)
            operate(project, "start")
            Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(project / "sprite.png")
            (project / "source.json").write_text(json.dumps({"width": 4, "height": 4, "style": "lineless", "ops": [{"op": "rect", "x": 0, "y": 0, "w": 4, "h": 4, "color": "#ff0000"}]}))
            base = {"source_path": "source.json", "image_path": "sprite.png", "evidence": [{"path": "sprite.png"}, {"path": "source.json"}]}
            response = root / "response.json"

            def submit(extra):
                response.write_text(json.dumps({**base, **extra}))
                task = operate(project, "next")
                return operate(project, "submit", task["task_id"], response)

            submit({"category": "item", "native_size": [4, 4], "art_direction": "Compact shapes", "functional_requirements": []})
            submit({"proposals": [{"id": str(i), "structure": f"Structure {i}"} for i in range(6)], "selected_id": "0"})
            for _ in range(3):
                submit({})
                result = submit({"context_id": "reviewer", "author_context_id": "author", "native_resolution": True, "integer_zoom": 3,
                                 "criteria": {name: {"score": 2, "observation": "Same unresolved defect", "evidence_indices": [0]} for name in CRITERIA}})
            self.assertEqual(result["stage"], "alternatives")
            self.assertEqual(result["usage"]["rendered_revisions"], 3)
            self.assertEqual(result["usage"]["visual_reviews"], 3)
            changed = json.loads((project / "brief.json").read_text())
            changed["goal"] = "Changed project direction"
            (project / "brief.json").write_text(json.dumps(changed))
            reopened = operate(project, "resume")
            self.assertEqual(reopened["stage"], "contract")
            self.assertEqual(reopened["usage"]["visual_reviews"], 3)

    def test_rejection_reopens_construction_and_preserves_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "input.json"
            brief.write_text(json.dumps({"goal": "Test repairs", "budgets": {"rendered_revisions": 1}}))
            project = root / "project"
            initialize(project, brief)
            operate(project, "start")
            (project / "evidence.txt").write_text("Test evidence")
            Image.new("RGBA", (32, 32), (80, 140, 60, 255)).save(project / "art.png")
            (project / "source.json").write_text(json.dumps({"width": 32, "height": 32, "style": "lineless", "ops": [{"op": "rect", "x": 0, "y": 0, "w": 32, "h": 32, "color": "#508c3c"}]}))
            response = root / "response.json"
            base = {"source_path": "source.json", "image_path": "art.png", "evidence": [{"path": "evidence.txt"}, {"path": "art.png"}, {"path": "source.json"}]}
            for extra in (
                {"category": "item", "native_size": [32, 32], "art_direction": "Clear masses", "functional_requirements": []},
                {"proposals": [{"id": str(i), "structure": f"Structure {i}"} for i in range(6)], "selected_id": "0"},
                {},
            ):
                response.write_text(json.dumps({**base, **extra}))
                task = operate(project, "next")
                operate(project, "submit", task["task_id"], response)
            review = {**base, "context_id": "reviewer", "author_context_id": "author", "native_resolution": True, "integer_zoom": 3,
                      "criteria": {name: {"score": 2, "observation": "Visible structural defect", "evidence_indices": [0]} for name in CRITERIA}}
            response.write_text(json.dumps(review))
            task = operate(project, "next")
            result = operate(project, "submit", task["task_id"], response)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["usage"]["rendered_revisions"], 1)
            self.assertEqual(result["usage"]["visual_reviews"], 1)
            self.assertEqual(result["reason"], "Budget exhausted: rendered_revisions")

    def test_resume_order_and_no_attestation_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief = root / "input.json"
            brief.write_text(json.dumps({"goal": "Create a readable potion"}))
            project = root / "project"
            initialize(project, brief)
            first = operate(project, "start")
            self.assertIn("quality_protocol", first)
            self.assertEqual(first, operate(project, "start"))
            self.assertEqual(first, operate(project, "resume"))
            response = root / "response.json"
            evidence = project / "evidence.txt"
            evidence.write_text("Synthetic evidence; not artistic approval")
            Image.new("RGBA", (32, 32), (80, 140, 60, 255)).save(project / "art.png")
            (project / "source.json").write_text(json.dumps({"width": 32, "height": 32, "style": "lineless", "ops": [{"op": "rect", "x": 0, "y": 0, "w": 32, "h": 32, "color": "#508c3c"}]}))
            response.write_text(json.dumps({"evidence": [{"path": "evidence.txt"}]}))
            with self.assertRaises(ValueError):
                operate(project, "submit", 99, response)
            for _ in range(6):
                task = operate(project, "next")
                data = {"source_path": "source.json", "image_path": "art.png", "evidence": [{"path": "evidence.txt"}, {"path": "art.png"}, {"path": "source.json"}]}
                if task["stage"] == "contract":
                    data.update(category="item", native_size=[32, 32], art_direction="Readable clean clusters", functional_requirements=[])
                elif task["stage"] == "alternatives":
                    data.update(proposals=[{"id": str(i), "structure": f"Distinct structural proposal {i}"} for i in range(6)], selected_id="0")
                elif task["stage"] in ("art_review", "context_review"):
                    data.update(context_id=task["stage"], author_context_id="author", native_resolution=True, integer_zoom=3,
                                criteria={name: {"score": 3, "observation": "Synthetic test observation", "evidence_indices": [0]} for name in CRITERIA})
                response.write_text(json.dumps(data))
                operate(project, "submit", task["task_id"], response)
            final = operate(project, "status")
            self.assertEqual(final["status"], "blocked")
            self.assertFalse(final["approval_supported"])
            archived = project / ".pixelai" / "artifacts" / hashlib.sha256(evidence.read_bytes()).hexdigest()
            self.assertEqual(archived.read_bytes(), evidence.read_bytes())
            evidence.write_text("Changed evidence")
            self.assertEqual(operate(project, "resume")["stage"], "contract")
            self.assertNotEqual(archived.read_bytes(), evidence.read_bytes())

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

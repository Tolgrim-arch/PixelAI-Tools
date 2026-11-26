"""Scores remain source-bound and required delivery beats cannot be omitted."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from pixelai.cli import main
from pixelai.delivery import verify_delivery
from pixelai.evidence import bind_evidence
from pixelai.manifest import load_manifest, simulate
from pixelai.provenance import verify_construction
from pixelai.review_packet import prepare_packet
from pixelai.runtime import render_scene


class ScoredExportTest(unittest.TestCase):
    def test_score_provenance_delivery_review_and_event_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            score = {"schema_version": 1, "intent": "AUTHOR INTENT DO NOT LEAK",
                     "beats": [{"name": name, "purpose": "AUTHOR PURPOSE DO NOT LEAK", "start": i, "end": i+1}
                               for i, name in enumerate(("anticipation", "impact", "recovery"))],
                     "events": [{"id": "hit", "name": "damage", "at_ms": 100, "socket": "tool"}]}
            spec = {"asset_id": "hero", "width": 8, "height": 8, "style": "lineless",
                    "frames": [{"ops": [{"op": "pixel", "x": x, "y": 3, "color": "#44aa66"}]} for x in (2, 4, 3)],
                    "runtime": {"pivot": [4, 8], "ground_anchor": [4, 8], "sort_origin": [4, 8], "sockets": {"tool": [5, 3]}},
                    "durations_ms": [100, 50, 200], "clips": {"strike": {"frames": [0, 1, 2], "loop": True, "score": score}}}
            (root / "source.json").write_text(json.dumps(spec))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["render", str(root / "source.json"), "-o", str(root / "sheet.png"), "--manifest", str(root / "asset.json"), "--json"]), 0)
            manifest, _ = load_manifest(root / "asset.json")
            self.assertEqual(manifest["clips"]["strike"]["score"], score)
            submission = {"source_path": "source.json", "image_path": "sheet.png", "manifest_path": "asset.json",
                          "evidence": bind_evidence(root, [{"path": name} for name in ("source.json", "sheet.png", "asset.json")])}
            verify_construction(root, submission)
            delivery = {"animation_scores": {"strike": {"beats": ["anticipation", "impact", "recovery"], "events": ["hit"]}}}
            self.assertEqual(verify_delivery(root / "asset.json", delivery)["status"], "covered")
            with self.assertRaisesRegex(ValueError, "Missing score events"):
                verify_delivery(root / "asset.json", {"animation_scores": {"strike": {"events": ["missing"]}}})
            contract = {"category": "human", "native_size": [8, 8], "art_direction": "Clear clusters", "delivery": delivery}
            packet = prepare_packet(root, contract, submission, "context_review")
            self.assertNotIn("AUTHOR", json.dumps(packet))
            self.assertEqual(packet["animation_timing"]["strike"]["beats"][1]["start_ms"], 100)
            self.assertEqual(simulate(root / "asset.json")["score_beats"]["strike"][2]["end_ms"], 350)
            scene = {"schema_version": 1, "width": 32, "height": 32, "times_ms": [0, 100, 450],
                     "actors": [{"id": "hero", "manifest": "asset.json", "clip": "strike", "position": [16, 16]}],
                     "expectations": [{"time_ms": 450, "actor": "hero", "event": "hit"}]}
            (root / "scene.json").write_text(json.dumps(scene))
            report = render_scene(root / "scene.json", root / "passed")
            self.assertEqual([event["time_ms"] for event in report["animation_events"]], [100, 450])
            self.assertEqual(report["scenario"]["status"], "passed")
            scene["expectations"][0]["event"] = "missing"
            (root / "scene.json").write_text(json.dumps(scene))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scene", str(root / "scene.json"), "--output", str(root / "failed")]), 1)
            tampered = deepcopy(manifest)
            tampered["clips"]["strike"]["score"]["events"][0]["at_ms"] = 101
            (root / "asset.json").write_text(json.dumps(tampered))
            with self.assertRaisesRegex(ValueError, "clips do not match"):
                verify_construction(root, submission)
            del tampered["clips"]["strike"]["score"]
            (root / "asset.json").write_text(json.dumps(tampered))
            with self.assertRaisesRegex(ValueError, "Missing animation score"):
                verify_delivery(root / "asset.json", delivery)

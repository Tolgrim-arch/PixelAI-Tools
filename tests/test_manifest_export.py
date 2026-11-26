"""Universal export integrates transformed anchors and managed provenance."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from pixelai.cli import main
from pixelai.manifest import load_manifest
from pixelai.provenance import verify_construction


class ManifestExportTest(unittest.TestCase):
    def test_derived_runtime_override_precedence_and_ambiguity(self):
        from pixelai.runner import run_frames
        spec = {"width": 64, "height": 64, "frame_count": 2, "style": "lineless", "ops": [
            {"op": "char_rig", "size": 64, "pose": "walk", "morphology": {"body_plan": "stocky"}}],
                "runtime": {"derive": "structure", "pivot": [33, 56], "sockets": {"custom": [10, 10]},
                            "frame_overrides": {"1": {"pivot": [34, 56], "sockets": {"custom": [12, 14]}}}}}
        frames, _ = run_frames(spec)
        first = next(record for record in frames[0].attachments if record["type"] == "runtime")
        second = next(record for record in frames[1].attachments if record["type"] == "runtime")
        self.assertEqual(first["pivot"], [33, 56])
        self.assertEqual(second["pivot"], [34, 56])
        self.assertEqual(second["sockets"]["custom"], [12, 14])
        self.assertIn("arm_1_hand", second["sockets"])
        spec["ops"].append(dict(spec["ops"][0]))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            run_frames(spec)

    def test_structure_derived_anchors_and_sockets_match_fitted_rig(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = {"asset_id": "heavy-worker", "width": 64, "height": 64, "style": "ext_outline", "frame_count": 4,
                    "ops": [{"op": "char_rig", "size": 64, "dir": "left", "pose": "attack", "shadow": False,
                             "morphology": {"body_plan": "heavy"}}], "runtime": {"derive": "structure", "state": "healthy"}}
            source = root / "source.json"
            source.write_text(json.dumps(spec))
            with redirect_stdout(io.StringIO()):
                rc = main(["render", str(source), "-o", str(root / "sheet.png"), "--manifest", str(root / "asset.json"), "--json"])
            self.assertEqual(rc, 0)
            manifest, _ = load_manifest(root / "asset.json")
            from pixelai.runner import run_frames
            rendered, _ = run_frames(spec)
            for frame, canvas in zip(manifest["frames"], rendered):
                graph = next(record for record in canvas.attachments if record["type"] == "anatomy_graph")
                self.assertEqual(frame["pivot"], [32, 56])
                self.assertEqual(frame["view"], "left")
                self.assertEqual(frame["action"], "attack")
                for node in graph["nodes"]:
                    if node["role"] in ("hand", "foot"):
                        self.assertEqual(frame["sockets"][node["id"]], node["point"])
            verify_construction(root, {"source_path": "source.json", "image_path": "sheet.png", "manifest_path": "asset.json",
                                      "evidence": [{"path": path} for path in ("source.json", "sheet.png", "asset.json")]})

    def test_render_manifest_preserves_transformed_runtime_and_timing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = {"asset_id": "hero", "width": 8, "height": 8, "style": "lineless",
                    "frames": [{"ops": [{"op": "pixel", "x": x, "y": 3, "color": "#44aa66"}]} for x in (2, 4)],
                    "runtime": {"pivot": [4.0, 8.0], "ground_anchor": [4, 8], "sort_origin": [4, 8]},
                    "durations_ms": [100, 300], "clips": {"idle": {"frames": [0, 1], "loop": True}},
                    "post": [{"op": "pad", "size": 1}, {"op": "scale", "factor": 2}]}
            source = root / "source.json"
            source.write_text(json.dumps(spec))
            output = io.StringIO()
            with redirect_stdout(output):
                rc = main(["render", str(source), "-o", str(root / "sheet.png"), "--columns", "1", "--manifest", str(root / "asset.json"), "--json"])
            self.assertEqual(rc, 0)
            manifest, image = load_manifest(root / "asset.json")
            self.assertEqual(manifest["frames"][0]["pivot"], [10.0, 18.0])
            self.assertEqual(manifest["frames"][1]["rect"], [0, 20, 20, 20])
            self.assertEqual(image.size, (20, 40))
            data = {"source_path": "source.json", "image_path": "sheet.png", "manifest_path": "asset.json",
                    "evidence": [{"path": name} for name in ("source.json", "sheet.png", "asset.json")]}
            verify_construction(root, data, [20, 20])
            manifest["frames"][0]["pivot"] = [0, 0]
            (root / "asset.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "runtime pivot"):
                verify_construction(root, data)

    def test_missing_runtime_fails_before_writing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text(json.dumps({"width": 8, "height": 8, "asset_id": "test", "ops": []}))
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                rc = main(["render", str(source), "-o", str(root / "sheet.png"), "--manifest", str(root / "asset.json")])
            self.assertEqual(rc, 1)
            self.assertFalse((root / "sheet.png").exists())

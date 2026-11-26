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

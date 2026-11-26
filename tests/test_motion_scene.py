"""Exported scene assertions must fail when movement violates the contract."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.cli import main
from pixelai.runtime import render_scene


class MotionSceneTest(unittest.TestCase):
    def test_exported_collision_response_and_failed_assertions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGBA", (4, 4), (60, 140, 80, 255)).save(root / "sprite.png")
            manifest = {"schema_version": 1, "asset_id": "body", "texture": "sprite.png",
                        "texture_sha256": hashlib.sha256((root / "sprite.png").read_bytes()).hexdigest(),
                        "frames": [{"id": "0", "rect": [0, 0, 4, 4], "duration_ms": 100, "pivot": [2, 4],
                                    "ground_anchor": [2, 4], "sort_origin": [2, 4], "sockets": {"foot": [2, 4]},
                                    "regions": [{"id": "body", "role": "collision", "polygon": [[0, 0], [4, 0], [4, 4], [0, 4]]}]}],
                        "clips": {"idle": {"frames": ["0"], "loop": True}}}
            (root / "asset.json").write_text(json.dumps(manifest))
            scene = {"schema_version": 1, "width": 40, "height": 24, "collision_mode": "block", "times_ms": [0, 200],
                     "actors": [{"id": "hero", "manifest": "asset.json", "clip": "idle", "position": [10, 10], "velocity": [100, 0]},
                                {"id": "wall", "manifest": "asset.json", "clip": "idle", "position": [20, 10]}],
                     "expectations": [{"time_ms": 200, "actor": "hero", "position": [16, 10], "clip": "idle", "contacted": "wall", "before": "wall"}],
                     "planted_contacts": [{"actor": "wall", "socket": "foot", "start_ms": 0, "end_ms": 200}]}
            path = root / "scene.json"
            path.write_text(json.dumps(scene))
            report = render_scene(path, root / "good")
            self.assertEqual(report["scenario"]["status"], "passed")
            self.assertEqual(report["scenario"]["assertions"], 4)
            self.assertEqual(report["planted_contacts"]["status"], "passed")
            self.assertEqual(report["trace"][-1]["region_overlaps"], [])
            scene["expectations"][0]["position"] = [30, 10]
            path.write_text(json.dumps(scene))
            with redirect_stdout(io.StringIO()):
                rc = main(["scene", str(path), "--output", str(root / "failed"), "--json"])
            self.assertEqual(rc, 1)
            failure = json.loads((root / "failed/trace.json").read_text())
            self.assertEqual(failure["scenario"]["status"], "failed")
            self.assertEqual(failure["scenario"]["failures"][0]["actual"], [16, 10])
            scene["expectations"][0]["position"] = [16, 10]
            scene["planted_contacts"][0]["actor"] = "hero"
            path.write_text(json.dumps(scene))
            with redirect_stdout(io.StringIO()):
                rc = main(["scene", str(path), "--output", str(root / "sliding"), "--json"])
            self.assertEqual(rc, 1)
            sliding = json.loads((root / "sliding/trace.json").read_text())
            self.assertEqual(sliding["scenario"]["status"], "passed")
            episode = sliding["planted_contacts"]["episodes"][0]
            self.assertEqual(episode["max_drift_px"], 6)
            self.assertEqual(episode["observations"], 201)

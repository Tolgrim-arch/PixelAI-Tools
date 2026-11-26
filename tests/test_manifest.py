"""Universal contract tests use exported pixels, not renderer internals."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.manifest import simulate


class ManifestTest(unittest.TestCase):
    def test_exported_timing_and_stale_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            texture = root / "sheet.png"
            Image.new("RGBA", (8, 4), (40, 160, 70, 255)).save(texture)
            frames = [{"id": str(i), "rect": [i * 4, 0, 4, 4], "duration_ms": t,
                       "pivot": [2, 4], "ground_anchor": [2, 4], "sort_origin": [2, 4]}
                      for i, t in enumerate((100, 250))]
            data = {"schema_version": 1, "asset_id": "test", "texture": "sheet.png",
                    "texture_sha256": hashlib.sha256(texture.read_bytes()).hexdigest(),
                    "frames": frames, "clips": {"idle": {"frames": ["0", "1"], "loop": True}}}
            manifest = root / "asset.json"
            manifest.write_text(json.dumps(data))
            report = simulate(manifest)
            self.assertEqual([t["start_ms"] for t in report["trace"]], [0, 100])
            self.assertEqual(report["trace"][1]["duration_ms"], 250)
            for change in ("region", "clip", "duration", "pivot"):
                candidate = json.loads(json.dumps(data))
                if change == "region":
                    candidate["frames"][0]["rect"] = [7, 0, 4, 4]
                elif change == "clip":
                    candidate["clips"]["idle"]["frames"] = ["missing"]
                elif change == "duration":
                    candidate["frames"][0]["duration_ms"] = 0
                else:
                    candidate["frames"][0]["pivot"] = [float("nan"), 0]
                manifest.write_text(json.dumps(candidate))
                with self.assertRaises(ValueError):
                    simulate(manifest)
            manifest.write_text(json.dumps(data))
            Image.new("RGBA", (8, 4)).save(texture)
            with self.assertRaisesRegex(ValueError, "stale"):
                simulate(manifest)

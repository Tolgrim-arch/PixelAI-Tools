"""Required gameplay combinations cannot be replaced by relabeled files."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.delivery import verify_delivery


class DeliveryTest(unittest.TestCase):
    def test_missing_states_combinations_and_identical_views(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGBA", (8, 4), (50, 140, 70, 255)).save(root / "sheet.png")
            data = {"schema_version": 1, "asset_id": "hero", "texture": "sheet.png",
                    "texture_sha256": hashlib.sha256((root / "sheet.png").read_bytes()).hexdigest(),
                    "frames": [{"id": str(i), "rect": [4*i, 0, 4, 4], "duration_ms": 100,
                                "pivot": [2, 4], "ground_anchor": [2, 4], "sort_origin": [2, 4],
                                "view": view, "action": "idle", "state": "healthy"} for i, view in enumerate(("down", "up"))],
                    "clips": {"idle": {"frames": ["0", "1"], "loop": True}}}
            path = root / "asset.json"
            path.write_text(json.dumps(data))
            self.assertEqual(verify_delivery(path, {"views": ["down", "up"], "states": ["healthy"]})["status"], "covered")
            for delivery, message in (({"states": ["hurt"]}, "Missing states"),
                                      ({"required_combinations": [{"view": "up", "action": "attack"}]}, "combination"),
                                      ({"views": ["down", "up"], "distinct_views": True}, "identical")):
                with self.assertRaisesRegex(ValueError, message):
                    verify_delivery(path, delivery)
            data["clips"]["idle"]["frames"] = ["0"]
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Missing views"):
                verify_delivery(path, {"views": ["up"]})

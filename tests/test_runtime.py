"""Reference playback checks actual exported timing and contextual placement."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.runtime import actor_track, frame_at, render_scene


class RuntimeTest(unittest.TestCase):
    def test_context_frames_follow_durations_pivots_and_y_sorting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            texture = Image.new("RGBA", (8, 4), (255, 0, 0, 255))
            texture.paste(Image.new("RGBA", (4, 4), (0, 255, 0, 255)), (4, 0))
            texture.save(root / "sheet.png")
            data = {"schema_version": 1, "asset_id": "test", "texture": "sheet.png",
                    "texture_sha256": hashlib.sha256((root / "sheet.png").read_bytes()).hexdigest(),
                    "frames": [{"id": str(i), "rect": [4*i, 0, 4, 4], "duration_ms": duration,
                                "pivot": [2, 4], "sort_origin": [2, 4], "ground_anchor": [2, 4],
                                "regions": [{"id": "body", "role": "collision", "polygon": [[0, 0], [4, 0], [4, 4], [0, 4]]}]}
                               for i, duration in enumerate((100, 300))],
                    "clips": {"loop": {"frames": ["0", "1"], "loop": True},
                              "hold": {"frames": ["1"], "loop": False}}}
            (root / "asset.json").write_text(json.dumps(data))
            self.assertEqual(frame_at(data, "loop", 399)["id"], "1")
            self.assertEqual(frame_at(data, "loop", 400)["id"], "0")
            self.assertEqual(frame_at(data, "hold", 10000)["id"], "1")
            scene = {"schema_version": 1, "width": 24, "height": 24, "times_ms": [0, 100],
                     "actors": [{"id": "front", "manifest": "asset.json", "clip": "hold", "position": [10, 11]},
                                {"id": "back", "manifest": "asset.json", "clip": "loop", "position": [10, 10]}]}
            (root / "scene.json").write_text(json.dumps(scene))
            result = render_scene(root / "scene.json", root / "preview")
            self.assertEqual([a["actor"] for a in result["trace"][0]["actors"]], ["back", "front"])
            self.assertEqual(result["trace"][0]["actors"][0]["origin"], [8, 6])
            self.assertEqual(len(result["trace"][0]["region_overlaps"]), 1)
            self.assertEqual(result["trace"][0]["region_overlaps"][0]["first"]["role"], "collision")
            with Image.open(root / "preview/scene_0000.png") as image:
                self.assertEqual(image.getpixel((9, 8)), (0, 255, 0, 255))
            with self.assertRaisesRegex(ValueError, "already exists"):
                render_scene(root / "scene.json", root / "preview")

    def test_declared_and_protected_transitions(self):
        data = {"frames": [{"id": "0", "duration_ms": 100}],
                "clips": {"idle": {"frames": ["0"], "loop": True},
                          "attack": {"frames": ["0"], "loop": False, "interruptible": False}},
                "transitions": [{"from": "idle", "to": "attack"}, {"from": "attack", "to": "idle"}]}
        actor = {"clip": "idle", "position": [10, 10], "timeline": [
            {"at_ms": 200, "clip": "attack"}, {"at_ms": 300, "clip": "idle", "position": [12, 10]}]}
        track = actor_track(actor, data)
        self.assertEqual(track[-1]["clip_started_ms"], 300)
        self.assertEqual(track[-1]["position"], [12, 10])
        actor["timeline"][1]["at_ms"] = 250
        with self.assertRaisesRegex(ValueError, "protected action"):
            actor_track(actor, data)
        actor["timeline"][1]["at_ms"] = 300
        data["transitions"] = []
        with self.assertRaisesRegex(ValueError, "Undeclared transition"):
            actor_track(actor, data)

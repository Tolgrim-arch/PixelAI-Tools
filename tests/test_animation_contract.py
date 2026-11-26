"""Exported holds and named actions retain their semantic timing."""

import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.animation_contract import clips_by_index, durations_ms
from pixelai.canvas import Canvas
from pixelai.exporter import export_gif, export_godot_tres, export_spritesheet


class AnimationContractTest(unittest.TestCase):
    def test_variable_durations_and_named_godot_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a, b = Canvas(4, 4), Canvas(4, 4)
            a.set_pixel(1, 1, (255, 0, 0, 255))
            b.set_pixel(2, 1, (0, 255, 0, 255))
            frames, times = [a, b], [100, 300]
            clips = {"idle": {"frames": [0], "loop": True}, "strike": {"frames": [0, 1], "loop": False}}
            sheet, metadata, tres = root / "sheet.png", root / "sheet.json", root / "sheet.tres"
            export_spritesheet(frames, sheet, meta_path=metadata, durations_ms=times, clips=clips)
            export_godot_tres(sheet, tres, frames, fps=10, durations_ms=times, clips=clips)
            data = json.loads(metadata.read_text())
            self.assertEqual([f["duration_ms"] for f in data["frames"]], times)
            self.assertEqual(data["clips"], clips)
            text = tres.read_text()
            self.assertIn('&"strike"', text)
            self.assertIn('"loop": false', text)
            self.assertIn('"duration": 3.0', text)
            gif = root / "animation.gif"
            export_gif(frames, gif, fps=10, durations_ms=times)
            with Image.open(gif) as image:
                self.assertEqual(image.info["duration"], 100)
                image.seek(1)
                self.assertEqual(image.info["duration"], 300)

    def test_invalid_timing_and_clip_indices(self):
        for times in ([100], [0, 100], [True, 100]):
            with self.assertRaises(ValueError):
                durations_ms(2, values=times)
        with self.assertRaises(ValueError):
            clips_by_index(2, {"bad": {"frames": [2], "loop": True}})

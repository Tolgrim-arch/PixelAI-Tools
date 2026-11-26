"""Construction evidence must match source pixels, timing and clip semantics."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pixelai.exporter import export_gif, export_spritesheet
from pixelai.provenance import verify_construction
from pixelai.runner import run_frames


class ProvenanceTest(unittest.TestCase):
    def test_atlas_pixels_durations_and_clips_are_source_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = {"width": 8, "height": 8, "style": "lineless", "durations_ms": [100, 300],
                    "frames": [{"ops": [{"op": "pixel", "x": x, "y": 3, "color": "#44aa66"}]} for x in (2, 5)],
                    "clips": {"move": {"frames": [0, 1], "loop": False}}}
            (root / "source.json").write_text(json.dumps(spec))
            frames, _ = run_frames(spec)
            export_spritesheet(frames, root / "sheet.png")
            manifest = {"schema_version": 1, "asset_id": "test", "texture": "sheet.png",
                        "texture_sha256": hashlib.sha256((root / "sheet.png").read_bytes()).hexdigest(),
                        "frames": [{"id": str(i), "rect": [8*i, 0, 8, 8], "duration_ms": t,
                                    "pivot": [4, 8], "ground_anchor": [4, 8], "sort_origin": [4, 8]}
                                   for i, t in enumerate((100, 300))],
                        "clips": {"move": {"frames": ["0", "1"], "loop": False}}}
            path = root / "manifest.json"
            path.write_text(json.dumps(manifest))
            submission = {"source_path": "source.json", "image_path": "sheet.png", "manifest_path": "manifest.json",
                          "evidence": [{"path": name} for name in ("source.json", "sheet.png", "manifest.json")]}
            verify_construction(root, submission)
            for defect in ("pixels", "duration", "clip"):
                candidate = json.loads(json.dumps(manifest))
                if defect == "pixels":
                    candidate["frames"][0]["rect"] = [8, 0, 8, 8]
                elif defect == "duration":
                    candidate["frames"][0]["duration_ms"] = 200
                else:
                    candidate["clips"]["move"]["loop"] = True
                path.write_text(json.dumps(candidate))
                with self.assertRaisesRegex(ValueError, "match"):
                    verify_construction(root, submission)

    def test_gif_palette_conversion_and_timing_are_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = {"width": 8, "height": 8, "style": "lineless", "durations_ms": [100, 300],
                    "frames": [{"ops": [{"op": "pixel", "x": x, "y": 2, "color": "#4488bb"}]} for x in (2, 4)]}
            (root / "source.json").write_text(json.dumps(spec))
            frames, _ = run_frames(spec)
            export_gif(frames, root / "preview.gif", durations_ms=[100, 300])
            submission = {"source_path": "source.json", "image_path": "preview.gif",
                          "evidence": [{"path": "source.json"}, {"path": "preview.gif"}]}
            verify_construction(root, submission)
            export_gif(frames, root / "preview.gif", durations_ms=[100, 100])
            with self.assertRaisesRegex(ValueError, "timing"):
                verify_construction(root, submission)

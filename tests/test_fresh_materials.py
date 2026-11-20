import unittest
import contextlib
import io
import json
import tempfile
from pathlib import Path

from pixelai.canvas import Canvas
from pixelai.materials import PATTERNS
from pixelai.runner import run_frames, run_layers
from pixelai.cli import main


class FreshGenerationTest(unittest.TestCase):
    def test_cli_fresh_rejects_import_without_writing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "new.json"
            source.write_text(json.dumps({"width": 8, "height": 8,
                "ops": [{"op": "load_png", "path": "discarded.png"}]}))
            for args in (["validate", str(source), "--fresh"],
                         ["render", str(source), "--fresh", "-o", str(root / "out.png")]):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    self.assertEqual(main(args), 1)
                self.assertIn("fresh generation forbids", stderr.getvalue())
            self.assertFalse((root / "out.png").exists())

    def test_fresh_requires_boolean(self):
        with self.assertRaisesRegex(ValueError, "fresh must be a boolean"):
            run_frames({"width": 8, "height": 8, "fresh": "false"})

    def test_reuse_rejected_before_reading_files(self):
        for fragment in (
            {"extends": "missing.png"},
            {"ops": [{"op": "load_png", "path": "missing.png"}]},
            {"defs": {"old": {"ops": [{"op": "load_png", "path": "missing.png"}]}}},
            {"frames": [{"ops": [{"op": "load_png", "path": "missing.png"}]}]},
            {"layers": [{"extends": "missing.json"}]},
            {"keyframes": [{"ops": [{"op": "load_png", "path": "missing.png"}]}]},
        ):
            for render in (run_frames, run_layers):
                with self.subTest(fragment=fragment, render=render.__name__):
                    with self.assertRaisesRegex(ValueError, "fresh generation forbids"):
                        render({"width": 16, "height": 16, "fresh": True, **fragment})

    def test_fresh_allows_new_local_components(self):
        frames, _ = run_frames({"width": 8, "height": 8, "fresh": True,
            "defs": {"dot": {"ops": [{"op": "pixel", "x": 2, "y": 2, "color": "#abcdef"}]}},
            "ops": [{"op": "stamp", "def": "dot"}]})
        self.assertEqual(frames[0].get_pixel(2, 2), (171, 205, 239, 255))


class MaterialTest(unittest.TestCase):
    def texture(self, pattern, density=1, seed=42):
        c = Canvas(32, 32)
        c.scatter(0, 0, 32, 32, (90, 120, 150, 255), pattern=pattern, density=density, seed=seed)
        return tuple(c.get_pixel(x, y) for y in range(32) for x in range(32))

    def test_materials_distinct_repeatable_seeded_and_density_controlled(self):
        outputs = []
        for pattern in sorted(PATTERNS | {"wood"}):
            with self.subTest(pattern=pattern):
                pixels = self.texture(pattern, .7)
                self.assertEqual(pixels, self.texture(pattern, .7))
                self.assertNotEqual(pixels, self.texture(pattern, .7, 98))
                self.assertTrue(any(p[3] for p in pixels))
                self.assertFalse(any(p[3] for p in self.texture(pattern, 0)))
                outputs.append(pixels)
        self.assertEqual(len(set(outputs)), len(outputs))

    def test_texture_respects_target_silhouette(self):
        for pattern in PATTERNS:
            c = Canvas(32, 32)
            c.draw_rect(8, 8, 16, 16, (20, 30, 40, 255))
            c.scatter(0, 0, 32, 32, (90, 120, 150, 255), pattern=pattern,
                      density=1, target_color=(20, 30, 40, 255))
            self.assertFalse(any(c.get_pixel(x, y)[3] for y in range(32)
                                 for x in range(32) if not (8 <= x < 24 and 8 <= y < 24)))

    def test_unknown_pattern_fails(self):
        with self.assertRaisesRegex(ValueError, "Unknown material"):
            self.texture("typo")

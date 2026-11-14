"""Unit tests for pixelai-tools MVP."""

import json
import tempfile
import unittest
from pathlib import Path

from pixelai.cli import main
from pixelai.color import parse_color, TRANSPARENT
from pixelai.runner import run_spec


class TestMVP(unittest.TestCase):
    def test_parse_color(self) -> None:
        self.assertEqual(parse_color("#ff00aa"), (255, 0, 170, 255))
        self.assertEqual(parse_color("#00ff0080"), (0, 255, 0, 128))
        self.assertEqual(parse_color("transparent"), TRANSPARENT)
        self.assertEqual(parse_color("ink", {"ink": (10, 20, 30, 255)}), (10, 20, 30, 255))

    def test_spec_primitives_mirror_outline_scale(self) -> None:
        spec = {
            "width": 8,
            "height": 8,
            "palette": {"a": "#ff0000", "o": "#000000"},
            "ops": [
                {"op": "pixel", "x": 1, "y": 1, "color": "a"},
                {"op": "mirror_x"},
            ],
            "post": [
                {"op": "outline", "color": "o"},
                {"op": "scale", "factor": 2},
            ],
        }
        canvas = run_spec(spec)
        self.assertEqual((canvas.width, canvas.height), (16, 16))
        # Mirrored pixel at (1,1) and (6,1), scaled 2x -> (2,2) and (12,2)
        self.assertEqual(canvas.get_pixel(2, 2), (255, 0, 0, 255))
        self.assertEqual(canvas.get_pixel(12, 2), (255, 0, 0, 255))
        # Outline at (0,1) scaled 2x -> (0,2)
        self.assertEqual(canvas.get_pixel(0, 2), (0, 0, 0, 255))

    def test_cli_render_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = Path(tmp) / "s.json"
            out_path = Path(tmp) / "out.png"
            spec_path.write_text(
                json.dumps({
                    "width": 4,
                    "height": 4,
                    "ops": [{"op": "rect", "x": 1, "y": 1, "w": 2, "h": 2, "color": "#00ff00"}],
                }),
                encoding="utf-8",
            )
            rc = main(["render", str(spec_path), "-o", str(out_path)])
            self.assertEqual(rc, 0)
            self.assertTrue(out_path.exists())
            self.assertGreater(out_path.stat().st_size, 0)

    def test_builtin_palette_and_grid(self) -> None:
        spec = {
            "width": 4,
            "height": 4,
            "palette": "pico8",
            "ops": [
                {"op": "grid", "x": 1, "y": 1, "rows": ["8.", ".b"]},
            ],
        }
        canvas = run_spec(spec)
        self.assertEqual(canvas.get_pixel(1, 1), (255, 0, 77, 255))
        self.assertEqual(canvas.get_pixel(2, 1), TRANSPARENT)
        self.assertEqual(canvas.get_pixel(2, 2), (0, 228, 54, 255))


if __name__ == "__main__":
    unittest.main()

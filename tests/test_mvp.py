"""Unit tests for pixelai-tools v0.2."""

import json
import tempfile
import unittest
from pathlib import Path

from pixelai.cli import main
from pixelai.color import parse_color, TRANSPARENT
from pixelai.runner import run_frames, run_spec


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
        self.assertEqual(canvas.get_pixel(2, 2), (255, 0, 0, 255))
        self.assertEqual(canvas.get_pixel(12, 2), (255, 0, 0, 255))
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

    def test_dither_and_shade(self) -> None:
        spec = {
            "width": 6,
            "height": 6,
            "ops": [
                {"op": "dither", "x": 1, "y": 1, "w": 4, "h": 4, "color_a": "#808080", "color_b": "#404040"},
            ],
            "post": [{"op": "shade", "amount": 0.25}],
        }
        canvas = run_spec(spec)
        self.assertEqual(canvas.get_pixel(1, 1), (160, 160, 160, 255))
        self.assertEqual(canvas.get_pixel(4, 4), (96, 96, 96, 255))

    def test_iso_primitives(self) -> None:
        spec = {
            "width": 32,
            "height": 32,
            "palette": "cozy24",
            "ops": [
                {"op": "iso_box", "cx": 16, "cy": 14, "rx": 8, "h": 8, "top": "stone_l", "left": "stone", "right": "stone_d", "edge": "ink"},
                {"op": "iso_roof", "cx": 16, "cy": 14, "rx": 8, "h": 6, "style": "pyramid", "left": "roof_l", "right": "roof_d", "ridge": "ink"},
                {"op": "iso_wall_rect", "face": "left", "x": 12, "y": 17, "w": 3, "h": 4, "color": "ink"},
            ],
        }
        canvas = run_spec(spec)
        # Apex of pyramid roof at (16, 8) has ridge color 'ink' (#21181b)
        self.assertEqual(canvas.get_pixel(16, 8), (33, 24, 27, 255))
        # Door on left wall at (12, 17)
        self.assertEqual(canvas.get_pixel(12, 17), (33, 24, 27, 255))

    def test_defs_stamp_remap_and_scatter(self) -> None:
        spec = {
            "width": 8,
            "height": 8,
            "palette": {"a": "#ff0000", "b": "#0000ff", "g": "#00ff00"},
            "defs": {
                "dot": {
                    "width": 2,
                    "height": 2,
                    "ops": [{"op": "pixel", "x": 0, "y": 0, "color": "a"}],
                }
            },
            "ops": [
                {"op": "stamp", "def": "dot", "x": 0, "y": 0},
                {"op": "stamp", "def": "dot", "x": 2, "y": 0, "flip_x": True, "remap": {"a": "b"}},
                {"op": "scatter", "x": 0, "y": 0, "w": 8, "h": 8, "color": "g", "target_color": "b", "density": 1.0},
            ],
        }
        canvas = run_spec(spec)
        self.assertEqual(canvas.get_pixel(0, 0), (255, 0, 0, 255))
        # Flipped (0,0) in 2x2 becomes (1,0) -> placed at x=2+1=3, remapped to 'b' then scattered to 'g'
        self.assertEqual(canvas.get_pixel(3, 0), (0, 255, 0, 255))

    def test_animation_gif_and_spritesheet(self) -> None:
        spec = {
            "width": 4,
            "height": 4,
            "palette": "cozy24",
            "frames": [
                {"name": "f0", "ops": [{"op": "pixel", "x": 1, "y": 1, "color": "roof"}]},
                {"name": "f1", "ops": [{"op": "pixel", "x": 2, "y": 1, "color": "roof"}]},
            ],
        }
        frames, names = run_frames(spec)
        self.assertEqual(len(frames), 2)
        self.assertEqual(names, ["f0", "f1"])

        with tempfile.TemporaryDirectory() as tmp:
            spec_p = Path(tmp) / "anim.json"
            gif_p = Path(tmp) / "anim.gif"
            sheet_p = Path(tmp) / "sheet.png"
            meta_p = Path(tmp) / "sheet.json"
            spec_p.write_text(json.dumps(spec), encoding="utf-8")

            self.assertEqual(main(["render", str(spec_p), "-o", str(gif_p), "--fps", "6"]), 0)
            self.assertTrue(gif_p.exists())

            self.assertEqual(
                main(["render", str(spec_p), "-o", str(sheet_p), "--meta", str(meta_p)]),
                0,
            )
            self.assertTrue(sheet_p.exists())
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
            self.assertEqual(len(meta["frames"]), 2)
            self.assertEqual(meta["frames"][1]["x"], 4)

    def test_cli_guide(self) -> None:
        self.assertEqual(main(["guide"]), 0)


if __name__ == "__main__":
    unittest.main()

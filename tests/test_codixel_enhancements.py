"""Tests for Codixel-inspired pixel art enhancements in pixelai-tools."""

import json
import math
import tempfile
import unittest
from pathlib import Path

from pixelai import cli, deform, filters, inspect_tool, organic
from pixelai.canvas import Canvas
from pixelai.color import dither_band_index, hue_ramp, luminance
from pixelai.exporter import export_png
from pixelai.runner import run_frames, run_spec


class TestCodixelEnhancements(unittest.TestCase):
    def test_cleanup_removes_orphan_and_preserves_high_contrast_eye(self):
        c = Canvas(12, 12)
        base = (180, 140, 100, 255)
        stray = (185, 142, 102, 255)  # within tol=60
        eye = (20, 15, 25, 255)  # high contrast, dist > 60
        c.draw_rect(2, 2, 6, 6, base, filled=True)
        c.set_pixel(4, 4, stray)
        c.set_pixel(6, 4, eye)
        c.set_pixel(11, 11, base)  # isolated 1px orphan

        cleaned = filters.cleanup(c, tol=60.0, keep_lone=False)
        self.assertEqual(cleaned.get_pixel(11, 11)[3], 0)
        self.assertEqual(cleaned.get_pixel(4, 4), base)
        self.assertEqual(cleaned.get_pixel(6, 4), eye)

    def test_pixel_perfect_removes_l_step_corners(self):
        c = Canvas(8, 8)
        ink = (30, 20, 30, 255)
        # Staircase diagonal with L-corners: (1,1)-(2,1)-(2,2)-(3,2)-(3,3)
        for px, py in ((1, 1), (2, 1), (2, 2), (3, 2), (3, 3)):
            c.set_pixel(px, py, ink)
        pp = filters.pixel_perfect(c)
        self.assertEqual(pp.get_pixel(2, 1)[3], 0)
        self.assertEqual(pp.get_pixel(3, 2)[3], 0)
        self.assertEqual(pp.get_pixel(1, 1), ink)
        self.assertEqual(pp.get_pixel(2, 2), ink)
        self.assertEqual(pp.get_pixel(3, 3), ink)

    def test_edge_check_detects_nubs_strips_and_holes(self):
        c = Canvas(12, 12)
        col = (100, 180, 90, 255)
        c.draw_rect(3, 3, 5, 5, col, filled=True)
        c.set_pixel(5, 5, (0, 0, 0, 0))  # 1px pinhole
        c.set_pixel(8, 5, col)  # 1px nub
        c.set_pixel(9, 5, col)  # turns (8,5) into strip and (9,5) into nub

        edges = inspect_tool.edge_check(c)
        self.assertIn([5, 5], edges["holes"])
        self.assertIn([8, 5], edges["strips"])
        self.assertIn([9, 5], edges["nubs"])

        stats = inspect_tool.analyze_canvas(c)
        self.assertEqual(stats["edge_quality"]["holes"], 1)
        self.assertGreaterEqual(stats["edge_quality"]["strips"], 1)
        self.assertGreaterEqual(stats["edge_quality"]["nubs"], 1)

    def test_band_edge_bayer4_dithering_and_hue_ramp(self):
        ramp = hue_ramp(5, hue=120.0, shift=50.0)
        self.assertEqual(len(ramp), 5)
        lums = [luminance(c) for c in ramp]
        self.assertLess(lums[0], lums[-1])

        # Mid-band values stay flat regardless of (x, y)
        flat_vals = {dither_band_index(0.02, 4, x, y, strip=0.33) for x in range(4) for y in range(4)}
        self.assertEqual(flat_vals, {0})

        # Transition boundary mixes adjacent bands
        edge_vals = {dither_band_index(0.5 / 3.0, 4, x, y, strip=0.33) for x in range(4) for y in range(4)}
        self.assertEqual(edge_vals, {0, 1})

        spec = {
            "width": 24,
            "height": 24,
            "style": "lineless",
            "ops": [
                {"op": "band_gradient", "x": 0, "y": 0, "w": 24, "h": 24, "hue_ramp": {"n": 4, "hue": 200}},
                {"op": "dither", "x": 2, "y": 2, "w": 8, "h": 8, "color_a": "#223344", "color_b": "#88aacc", "mode": "bayer4", "ratio": 0.25},
            ],
        }
        canvas = run_spec(spec)
        self.assertGreater(inspect_tool.analyze_canvas(canvas)["unique_colors"], 2)

    def test_rim_light_brightens_light_facing_edge_before_outline(self):
        ramp = [(40, 40, 60, 255), (90, 90, 120, 255), (160, 160, 200, 255)]
        c = Canvas(12, 12)
        c.draw_rect(3, 3, 6, 6, ramp[1], filled=True)
        lit = filters.rim_light(c, ramp=ramp, direction=(-1, -1), steps=1)
        # Top-left edge faces (-1, -1) light -> stepped up to ramp[2]
        self.assertEqual(lit.get_pixel(3, 3), ramp[2])
        self.assertEqual(lit.get_pixel(5, 3), ramp[2])
        self.assertEqual(lit.get_pixel(3, 5), ramp[2])
        # Bottom-right interior & shadow edge stay at ramp[1]
        self.assertEqual(lit.get_pixel(5, 5), ramp[1])
        self.assertEqual(lit.get_pixel(8, 8), ramp[1])

        # Also test via JSON spec post pipeline
        spec = {
            "width": 16,
            "height": 16,
            "style": "ext_outline",
            "ops": [{"op": "rect", "x": 4, "y": 4, "w": 8, "h": 8, "color": "#5a5a78"}],
            "post": [
                {"op": "cleanup"},
                {"op": "pixel_perfect"},
                {"op": "rim_light", "dir": [-1, -1], "steps": 1},
            ],
        }
        out = run_spec(spec)
        self.assertGreater(luminance(out.get_pixel(4, 4)), luminance((0x5A, 0x5A, 0x78, 255)))

    def test_2bone_ik_and_spine_bend_wave(self):
        jx, jy = deform.solve_ik_2bone(0.0, 0.0, 10.0, 0.0, 8.0, 8.0, direction=1)
        self.assertAlmostEqual(math.hypot(jx, jy), 8.0, places=3)
        self.assertAlmostEqual(math.hypot(10.0 - jx, -jy), 8.0, places=3)

        rest = [[4, 16], [14, 16], [24, 16]]
        waved_a = deform.wave_polyline(rest, t=0.0, amp=4.0, wavelength=16.0, anchor_from=0.0)
        waved_b = deform.wave_polyline(rest, t=0.25, amp=4.0, wavelength=16.0, anchor_from=0.0)
        self.assertEqual(len(waved_a), 3)
        self.assertNotEqual(waved_a[-1], waved_b[-1])

        spec = {
            "width": 32,
            "height": 32,
            "style": "lineless",
            "frame_count": 3,
            "defs": {
                "tail": {
                    "width": 32,
                    "height": 32,
                    "ops": [{"op": "rect", "x": 4, "y": 14, "w": 22, "h": 4, "color": "#cc5533"}],
                }
            },
            "ops": [
                {"op": "bend", "def": "tail", "rest": rest, "wave": {"amp": 3.5, "wavelength": 16.0, "from": 0.1}},
                {"op": "ik_limb", "start": [6, 6], "target": [18, 12], "l1": 8, "l2": 8, "color": "#ddaa77"},
            ],
        }
        frames, _ = run_frames(spec)
        self.assertEqual(len(frames), 3)
        self.assertNotEqual(frames[0].pixels, frames[1].pixels)
        self.assertGreater(inspect_tool.analyze_canvas(frames[0])["opaque_pixels"], 40)

    def test_organic_sdf_solid_and_fbm_flame_smoke(self):
        spec = {
            "width": 40,
            "height": 48,
            "style": "lineless",
            "frame_count": 2,
            "ops": [
                {
                    "op": "solid",
                    "primitives": [
                        {"type": "capsule", "ax": 20, "ay": 22, "bx": 20, "by": 36, "ra": 6, "rb": 8},
                        {"type": "ellipse", "x": 20, "y": 18, "rx": 6, "ry": 5},
                    ],
                    "hue_ramp": {"n": 5, "hue": 140},
                    "inflate": 4.0,
                    "dither_strip": 0.3,
                },
                {"op": "smoke", "x": 20, "ground": 24, "height": 20, "width": 2.5, "warp": 12.0},
                {"op": "flame", "x": 20, "ground": 34, "height": 18, "width": 6.0, "embers": 3},
            ],
        }
        frames, _ = run_frames(spec)
        self.assertEqual(len(frames), 2)
        self.assertGreater(inspect_tool.analyze_canvas(frames[0])["opaque_pixels"], 150)
        self.assertNotEqual(frames[0].pixels, frames[1].pixels)

    def test_ruler_and_cli_integration(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            spec_path = tmp_dir / "sprite.json"
            out_png = tmp_dir / "sprite.png"
            render_ruler_png = tmp_dir / "render_ruler.png"
            inspect_ruler_png = tmp_dir / "inspect_ruler.png"

            spec = {
                "width": 16,
                "height": 16,
                "ops": [
                    {"op": "circle", "cx": 8, "cy": 8, "r": 5, "color": "#44aa66", "filled": True},
                    {"op": "text", "x": 2, "y": 1, "text": "OK", "color": "#ffffff", "scale": 1},
                ],
            }
            spec_path.write_text(json.dumps(spec), encoding="utf-8")

            rc = cli.main(["render", str(spec_path), "-o", str(out_png), "--ruler", str(render_ruler_png), "--ruler-scale", "3", "--ruler-step", "4"])
            self.assertEqual(rc, 0)
            self.assertTrue(out_png.exists())
            self.assertTrue(render_ruler_png.exists())

            rc2 = cli.main(["inspect", str(out_png), "--ruler", str(inspect_ruler_png), "--ruler-scale", "4", "--ruler-step", "8"])
            self.assertEqual(rc2, 0)
            self.assertTrue(inspect_ruler_png.exists())

            ruler_canvas = inspect_tool.load_png_as_canvas(inspect_ruler_png)
            self.assertGreater(ruler_canvas.width, 16 * 4)
            self.assertGreater(ruler_canvas.height, 16 * 4)


if __name__ == "__main__":
    unittest.main()

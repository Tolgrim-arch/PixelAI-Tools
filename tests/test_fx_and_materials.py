"""Tests for reusable post-processing FX, material recoloring, directional selout, and library imports."""

import json
import tempfile
import unittest
from pathlib import Path

from pixelai import cli, filters, fx
from pixelai.canvas import Canvas
from pixelai.color import TRANSPARENT
from pixelai.exporter import export_png
from pixelai.runner import run_frames, run_spec


class TestFxAndMaterials(unittest.TestCase):
    def _apple_spec(self, **extra):
        spec = {
            "width": 24,
            "height": 24,
            "palette": "cozy24",
            "style": "ext_outline",
            "ops": [
                {"op": "item_rig", "kind": "apple", "x": 0, "y": 0, "size": 24, "shine": True}
            ],
        }
        spec.update(extra)
        return spec

    def test_sheen_sweep_mask_strict_and_animates(self):
        base = run_spec(self._apple_spec())
        frames = fx.apply_fx_pipeline(
            [base],
            [{"type": "sheen_sweep", "color": "#fff7b8", "width": 3, "blend": "add", "pause_frames": 2}],
            total_frames=8,
        )
        self.assertEqual(len(frames), 8)
        # Transparent background pixels in base must remain transparent in all frames
        bg_indices = [i for i, px in enumerate(base.pixels) if px[3] == 0]
        for frame in frames:
            for idx in bg_indices:
                self.assertEqual(frame.pixels[idx], TRANSPARENT)
        # Active sweep frames should differ from paused final frame
        self.assertNotEqual(frames[2].pixels, frames[7].pixels)

    def test_composable_fx_suite(self):
        base = run_spec(self._apple_spec())
        frames = fx.apply_fx_pipeline(
            [base],
            [
                {"type": "aura_glow", "color": "#ffe68090", "radius": 1},
                {"type": "float_bob", "amplitude": 2},
                {"type": "sparkle_glint", "count": 3, "seed": 7},
                {"type": "hit_flash", "frames": [0]},
            ],
            total_frames=8,
        )
        self.assertEqual(len(frames), 8)
        unique_frames = {tuple(f.pixels) for f in frames}
        self.assertGreaterEqual(len(unique_frames), 4)

    def test_bounce_and_wind_sway_keep_shadow_anchored(self):
        c = Canvas(16, 16)
        c.mark_shadow = True
        c.mark_no_outline = True
        c.draw_ellipse(8, 13, 4, 1, (33, 24, 27, 64), filled=True)
        c.mark_shadow = False
        c.mark_no_outline = False
        c.draw_rect(6, 5, 4, 7, (88, 156, 76, 255))

        bounced = fx.apply_bounce(c, frame_idx=2, total_frames=8, height=3, squash=True)
        swayed = fx.apply_wind_sway(c, frame_idx=2, total_frames=8, amplitude=1)
        for idx in c.shadow_pixels:
            self.assertEqual(bounced.pixels[idx], c.pixels[idx])
            self.assertEqual(swayed.pixels[idx], c.pixels[idx])

    def test_recolor_material_gold_apple(self):
        red_apple = run_spec(self._apple_spec())
        gold_apple = run_spec(self._apple_spec(material="gold_specular"))
        self.assertNotEqual(red_apple.pixels, gold_apple.pixels)
        # Gold apple should contain bright warm highlight tones (R > 230, G > 200)
        gold_highlights = [
            px for px in gold_apple.pixels if px[3] > 0 and px[0] > 230 and px[1] > 200
        ]
        self.assertTrue(gold_highlights)

    def test_directional_selout_and_style_profile(self):
        flat = run_spec(self._apple_spec())
        cozy = run_spec(self._apple_spec(style_profile="cozy_modern"))
        self.assertNotEqual(flat.pixels, cozy.pixels)
        # Directional selout should still keep a clean non-empty silhouette
        opaque = sum(1 for px in cozy.pixels if px[3] > 0)
        self.assertGreater(opaque, 50)

    def test_library_imports_and_ramp_shift(self):
        spec = {
            "width": 32,
            "height": 32,
            "imports": ["@foliage/leaf_clusters", "@fx/gold_enchant"],
            "style": "ext_outline",
            "ops": [
                {"op": "stamp", "def": "leaf_cluster_md", "x": 6, "y": 10, "ramp_shift": -1},
                {"op": "stamp", "def": "leaf_cluster_md", "x": 12, "y": 6, "ramp_shift": 1},
                {"op": "stamp", "def": "leaf_tuft", "x": 14, "y": 14},
            ],
        }
        frames, names = run_frames(spec)
        self.assertEqual(len(frames), 12)  # Inferred from sheen_sweep in @fx/gold_enchant
        self.assertEqual(names[0], "frame_0")

    def test_cli_fx_on_finished_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            png_path = tmp_dir / "apple.png"
            gif_path = tmp_dir / "golden_apple.gif"
            export_png(run_spec(self._apple_spec()), png_path)

            rc = cli.main([
                "fx",
                str(png_path),
                "-o",
                str(gif_path),
                "--preset",
                "@fx/gold_enchant",
                "--fps",
                "10",
            ])
            self.assertEqual(rc, 0)
            self.assertTrue(gif_path.exists())
            self.assertGreater(gif_path.stat().st_size, 200)


if __name__ == "__main__":
    unittest.main()

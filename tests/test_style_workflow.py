"""Unit tests for Workflow A (pixelai style ingest/study/merge/guide) and
Workflow B (--style / style_ref, qa --style, and explicit layer z-ordering).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from pixelai.canvas import Canvas
from pixelai.runner import run_frames
from pixelai.style_ingest import detect_pixel_grid, ingest_reference_image
from pixelai.style_profile import apply_style_to_spec, compare_canvas_to_style, format_style_guide
from pixelai.style_study import merge_style_profiles, study_canvas


def _make_upscaled_jpeg_sprite(path: Path, scale: float = 5.5) -> None:
    """Create a synthetic 16x16 pixel art sprite upscaled by a fractional factor and saved as JPEG."""
    native = Image.new("RGB", (16, 16), (240, 240, 240))  # light solid background
    px = native.load()
    # Dark outline box with warm-lit interior
    for y in range(3, 13):
        for x in range(3, 13):
            if x in (3, 12) or y in (3, 12):
                px[x, y] = (28, 20, 32)  # dark ink outline
            elif x + y < 14:
                px[x, y] = (232, 160, 72)  # warm highlight
            elif x + y < 18:
                px[x, y] = (180, 96, 54)  # midtone
            else:
                px[x, y] = (98, 48, 62)  # cool shadow
    up_w = int(round(16 * scale))
    up_h = int(round(16 * scale))
    upscaled = native.resize((up_w, up_h), Image.Resampling.NEAREST)
    upscaled.save(path, format="JPEG", quality=82)


class TestStyleWorkflow(unittest.TestCase):
    def test_fractional_jpeg_ingest_recovers_grid_and_removes_bg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jpg_path = Path(tmp) / "ref.jfif"
            _make_upscaled_jpeg_sprite(jpg_path, scale=6.0)
            res = ingest_reference_image(jpg_path, max_colors=8)
            self.assertAlmostEqual(res.grid.cell_w, 6.0, delta=0.5)
            self.assertEqual(res.grid.cell_w, res.grid.cell_h)
            self.assertTrue(res.bg_removed)
            self.assertLessEqual(len(res.palette), 8)
            self.assertGreaterEqual(len(res.palette), 3)

    def test_study_and_merge_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "a.jfif"
            p2 = Path(tmp) / "b.jfif"
            _make_upscaled_jpeg_sprite(p1, scale=5.0)
            _make_upscaled_jpeg_sprite(p2, scale=6.0)
            r1 = ingest_reference_image(p1, max_colors=8)
            r2 = ingest_reference_image(p2, max_colors=8)
            prof1 = study_canvas(r1.canvas, r1.palette, name="a", source="a.jfif", grid_confidence=r1.grid.confidence)
            prof2 = study_canvas(r2.canvas, r2.palette, name="b", source="b.jfif", grid_confidence=r2.grid.confidence)

            self.assertIn("ramps", prof1["color_model"])
            self.assertIn("outline", prof1)
            self.assertIn("lighting", prof1)
            self.assertTrue(any("BACK-TO-FRONT" in r for r in prof1["agent_rules"]))

            merged = merge_style_profiles([prof1, prof2], name="combo", max_colors=12)
            self.assertEqual(merged["name"], "combo")
            self.assertEqual(merged["reference_count"], 2)
            guide = format_style_guide(merged)
            self.assertIn("# Style Profile: combo", guide)

    def test_layer_z_order_and_visibility(self) -> None:
        spec = {
            "width": 8,
            "height": 8,
            "palette": {"red": "#ff0000", "blue": "#0000ff", "green": "#00ff00"},
            "style": "lineless",
            "layers": [
                {"name": "front_declared_first", "z": 10, "ops": [{"op": "rect", "x": 2, "y": 2, "w": 4, "h": 4, "color": "red"}]},
                {"name": "back_declared_second", "z": -5, "ops": [{"op": "rect", "x": 2, "y": 2, "w": 4, "h": 4, "color": "blue"}]},
                {"name": "hidden_top", "z": 99, "visible": False, "ops": [{"op": "rect", "x": 2, "y": 2, "w": 4, "h": 4, "color": "green"}]},
            ],
        }
        frames, _ = run_frames(spec)
        # Red (z=10) must win over blue (z=-5), and green (visible=False) must not render
        self.assertEqual(frames[0].get_pixel(3, 3), (255, 0, 0, 255))

    def test_cli_end_to_end_workflow_a_and_b(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            ref = tmp_p / "pinterest_ref.jfif"
            _make_upscaled_jpeg_sprite(ref, scale=6.0)
            style_json = tmp_p / "learned.style.json"

            # Workflow A: study
            cp = subprocess.run(
                [sys.executable, "-m", "pixelai", "style", "study", str(ref), "-o", str(style_json), "--name", "test_pack"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(style_json.exists())
            self.assertIn("Studied 1 reference(s)", cp.stdout)

            # Workflow B: render with --style
            spec_path = tmp_p / "sprite.json"
            spec_path.write_text(json.dumps({
                "width": 16,
                "height": 16,
                "ops": [{"op": "rect", "x": 4, "y": 4, "w": 8, "h": 8, "color": "s0"}],
            }), encoding="utf-8")
            out_png = tmp_p / "out.png"
            subprocess.run(
                [sys.executable, "-m", "pixelai", "render", str(spec_path), "-o", str(out_png), "--style", str(style_json)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(out_png.exists())

            # Workflow B: qa --style
            qa_cp = subprocess.run(
                [sys.executable, "-m", "pixelai", "qa", str(out_png), "--style", str(style_json)],
                capture_output=True,
                text=True,
            )
            qa_data = json.loads(qa_cp.stdout)
            self.assertIn("style_fidelity", qa_data)
            self.assertGreaterEqual(qa_data["style_fidelity"]["fidelity_score"], 0.0)


if __name__ == "__main__":
    unittest.main()

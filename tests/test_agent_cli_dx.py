"""Tests for AI-agent CLI DX improvements (field linting, JSON errors, schema/guide, diff, contact-sheet, histogram/deltas)."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from pixelai import cli, inspect_tool
from pixelai.runner import run_spec


class TestAgentCliDX(unittest.TestCase):
    def test_unknown_field_linting_with_fuzzy_suggestion(self):
        spec = {
            "width": 16,
            "height": 16,
            "style": "lineless",
            "ops": [
                {"op": "circle", "cx": 8, "cy": 8, "r": 4, "color": "#44aa66", "filed": True},
            ],
            "post": [
                {"op": "cleanup", "to": 50},
            ],
        }
        canvas = run_spec(spec)
        joined = " | ".join(canvas.warnings)
        self.assertIn("Unknown field 'filed' in op 'circle'", joined)
        self.assertIn("did you mean 'filled'?", joined)
        self.assertIn("Unknown field 'to' in post op 'cleanup'", joined)
        self.assertIn("did you mean 'tol'?", joined)

    def test_structured_json_error_on_render_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad_spec = Path(tmp) / "bad.json"
            bad_spec.write_text(json.dumps({"width": 16, "height": 16, "ops": [{"op": "nonexistent_op"}]}), encoding="utf-8")
            out_buf, err_buf = io.StringIO(), io.StringIO()
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                rc = cli.main(["render", str(bad_spec), "-o", str(Path(tmp) / "out.png"), "--json"])
            self.assertEqual(rc, 1)
            self.assertEqual(out_buf.getvalue(), "")
            payload = json.loads(err_buf.getvalue())
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["command"], "render")
            self.assertIn("nonexistent_op", payload["error"])

    def test_modular_guide_and_json_schema(self):
        buf_list = io.StringIO()
        with redirect_stdout(buf_list):
            rc = cli.main(["guide", "--list"])
        self.assertEqual(rc, 0)
        self.assertIn("`solid`", buf_list.getvalue())
        self.assertIn("`rim_light`", buf_list.getvalue())

        buf_op = io.StringIO()
        with redirect_stdout(buf_op):
            rc2 = cli.main(["guide", "--op", "solid"])
        self.assertEqual(rc2, 0)
        self.assertIn("# op: `solid`", buf_op.getvalue())
        self.assertIn("primitives", buf_op.getvalue())

        buf_schema = io.StringIO()
        with redirect_stdout(buf_schema):
            rc3 = cli.main(["schema"])
        self.assertEqual(rc3, 0)
        schema = json.loads(buf_schema.getvalue())
        self.assertEqual(schema["$schema"], "http://json-schema.org/draft-07/schema#")
        self.assertIn("solid", schema["properties"]["ops"]["items"]["properties"]["op"]["enum"])

    def test_diff_contact_sheet_histogram_and_frame_deltas(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            spec_a = tmp_dir / "a.json"
            spec_b = tmp_dir / "b.json"
            anim_spec = tmp_dir / "anim.json"
            png_a = tmp_dir / "a.png"
            png_b = tmp_dir / "b.png"
            diff_png = tmp_dir / "diff.png"
            anim_gif = tmp_dir / "anim.gif"
            contact_png = tmp_dir / "contact.png"

            spec_a.write_text(json.dumps({
                "width": 16, "height": 16, "style": "lineless",
                "ops": [{"op": "rect", "x": 3, "y": 3, "w": 10, "h": 10, "color": "#44aa66"}],
            }), encoding="utf-8")
            spec_b.write_text(json.dumps({
                "width": 16, "height": 16, "style": "lineless",
                "ops": [
                    {"op": "rect", "x": 3, "y": 3, "w": 10, "h": 10, "color": "#44aa66"},
                    {"op": "rect", "x": 6, "y": 6, "w": 4, "h": 4, "color": "#ffdd55"},
                ],
            }), encoding="utf-8")
            anim_spec.write_text(json.dumps({
                "width": 16, "height": 16, "style": "lineless", "frame_count": 4,
                "ops": [{"op": "flame", "x": 8, "ground": 14, "height": 10, "width": 4}],
            }), encoding="utf-8")

            self.assertEqual(cli.main(["render", str(spec_a), "-o", str(png_a)]), 0)
            self.assertEqual(cli.main(["render", str(spec_b), "-o", str(png_b)]), 0)

            buf_diff = io.StringIO()
            with redirect_stdout(buf_diff):
                rc_diff = cli.main(["diff", str(png_a), str(png_b), "-o", str(diff_png), "--scale", "3", "--json"])
            self.assertEqual(rc_diff, 0)
            self.assertTrue(diff_png.exists())
            diff_stats = json.loads(buf_diff.getvalue())
            self.assertEqual(diff_stats["changed_pixels"], 16)
            self.assertEqual(diff_stats["change_bbox"], {"x": 6, "y": 6, "w": 4, "h": 4})

            # Render animated GIF + contact sheet in one call
            self.assertEqual(
                cli.main(["render", str(anim_spec), "-o", str(anim_gif), "--contact-sheet", str(contact_png), "--contact-scale", "3"]),
                0,
            )
            self.assertTrue(anim_gif.exists())
            self.assertTrue(contact_png.exists())

            # Inspect GIF for color_histogram and frame_deltas
            stats, _ = inspect_tool.analyze_image_file(anim_gif)
            self.assertIn("color_histogram", stats)
            self.assertGreater(len(stats["color_histogram"]), 0)
            self.assertEqual(len(stats["frame_deltas"]), 3)
            self.assertGreater(stats["avg_frame_delta"], 0.0)


if __name__ == "__main__":
    unittest.main()

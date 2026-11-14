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
                {"op": "iso_box", "cx": 16, "cy": 14, "rx": 8, "h": 8, "top": "stone_l", "left": "stone", "right": "stone_d"},
                {"op": "iso_roof", "cx": 16, "cy": 14, "rx": 8, "h": 6, "style": "pyramid", "left": "roof_l", "right": "roof_d"},
                {"op": "iso_wall_rect", "face": "left", "x": 12, "y": 17, "w": 3, "h": 4, "color": "wood_d"},
            ],
        }
        canvas = run_spec(spec)
        # Apex of pyramid roof at (16, 8) has brightened lineless bevel of 'roof_l' (#e87858 = 232, 120, 88)
        self.assertGreater(canvas.get_pixel(16, 8)[0], 232)
        # Door on left wall at (12, 17) has recessed top lip (darkened 'wood_d')
        self.assertLess(canvas.get_pixel(12, 17)[0], 110)

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

    def test_iso_structure_sorting_and_selout(self) -> None:
        spec = {
            "width": 32,
            "height": 32,
            "palette": "cozy24",
            "ops": [
                {
                    "op": "iso_structure",
                    "origin_x": 16,
                    "origin_y": 18,
                    "items": [
                        # Declared first: upper keep at gz=6
                        {"type": "box", "gx": 0, "gy": 0, "gz": 6, "rx": 4, "h": 6, "top": "roof_l", "left": "roof", "right": "roof_d"},
                        # Declared second: lower base at gz=0 (must be drawn BEFORE gz=6!)
                        {"type": "box", "gx": 0, "gy": 0, "gz": 0, "rx": 8, "h": 6, "top": "stone_l", "left": "stone", "right": "stone_d"},
                    ],
                }
            ],
            "post": [
                {"op": "outline", "color": "ink", "selout": True},
            ],
        }
        canvas = run_spec(spec)
        # Upper keep center at (16, 18 - 6 = 12) must remain 'roof_l' (#e87858 = 232, 120, 88), not overwritten by 'stone_l'
        self.assertEqual(canvas.get_pixel(16, 12), (232, 120, 88, 255))

    def test_border_warning_and_auto_pad(self) -> None:
        spec = {
            "width": 4,
            "height": 4,
            "ops": [{"op": "pixel", "x": 0, "y": 0, "color": "#ff0000"}],
            "post": [{"op": "outline", "color": "#000000"}],
        }
        c_warn = run_spec(spec)
        self.assertEqual(len(c_warn.warnings), 1)

        spec["post"] = [{"op": "outline", "color": "#000000", "auto_pad": True}]
        c_pad = run_spec(spec)
        self.assertEqual((c_pad.width, c_pad.height), (6, 6))
        self.assertEqual(len(c_pad.warnings), 0)
        # Original pixel shifted to (1,1), outline at (1,0)
        self.assertEqual(c_pad.get_pixel(1, 0), (0, 0, 0, 255))

    def test_lineless_bevel_and_external_outline(self) -> None:
        base_spec = {
            "width": 32,
            "height": 32,
            "palette": "cozy24",
            "ops": [
                {"op": "iso_box", "cx": 16, "cy": 20, "rx": 12, "h": 2, "top": "grass", "left": "grass_d", "right": "soil_d", "bevel": True},
                {"op": "iso_box", "cx": 16, "cy": 14, "rx": 6, "h": 6, "top": "stone_l", "left": "stone", "right": "stone_d", "bevel": True, "ground_shadow": 2},
                {"op": "iso_wall_rect", "face": "left", "x": 12, "y": 16, "w": 3, "h": 4, "color": "wood_d", "recessed": True},
            ],
            "post": [{"op": "drop_shadow", "dx": 1, "dy": 1}],
        }
        c_lineless = run_spec(base_spec)
        # Center vertical ridge of the stone box at (16, 18) gets brightened from 'stone' (#828c9e = 130, 140, 158)
        self.assertGreater(c_lineless.get_pixel(16, 18)[0], 130)

        # Now add external outline only: internal ridge at (16, 18) must remain untouched!
        ext_spec = dict(base_spec, post=[{"op": "outline", "color": "ink"}])
        c_ext = run_spec(ext_spec)
        self.assertEqual(c_ext.get_pixel(16, 18), c_lineless.get_pixel(16, 18))

    def test_autotile_char_rig_iso_tilemap_and_godot_inspect(self) -> None:
        spec = {
            "width": 64,
            "height": 64,
            "palette": "cozy24",
            "defs": {
                "g": {
                    "width": 16,
                    "height": 8,
                    "ops": [{"op": "iso_tile", "cx": 8, "cy": 4, "rx": 7, "ry": 3, "color": "grass"}],
                }
            },
            "ops": [
                {"op": "autotile", "x": 0, "y": 0, "tile_size": 8, "inner": "water", "outer": "grass", "lip": "soil_d"},
                {"op": "tilemap", "mode": "iso", "x": 32, "y": 40, "tile_w": 16, "tile_h": 16, "rows": ["gg", "gg"]},
                {"op": "char_rig", "x": 32, "y": 16, "dir": "right", "pose": "work", "frame": 0, "hat": "wheat"},
            ],
        }
        canvas = run_spec(spec)
        # Autotile tile 0 (all outer) at (2,2) is grass/grass_hl (opaque)
        self.assertEqual(canvas.get_pixel(2, 2)[3], 255)
        # Char rig hat at (32+6, 16+2) is wheat
        self.assertEqual(canvas.get_pixel(38, 18), (242, 191, 82, 255))

        with tempfile.TemporaryDirectory() as tmp:
            spec_p = Path(tmp) / "rig.json"
            sheet_p = Path(tmp) / "rig.png"
            tres_p = Path(tmp) / "rig.tres"
            spec_p.write_text(json.dumps(spec), encoding="utf-8")
            self.assertEqual(
                main(["render", str(spec_p), "-o", str(sheet_p), "--godot", str(tres_p), "--ascii"]),
                0,
            )
            self.assertTrue(tres_p.exists())
            self.assertIn("SpriteFrames", tres_p.read_text(encoding="utf-8"))
            self.assertEqual(main(["inspect", str(sheet_p), "--ascii"]), 0)

    def test_png_embed_extract_extends_rotation_and_multires_rig(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base_spec_p = Path(tmp) / "base.json"
            base_png_p = Path(tmp) / "base.png"
            child_spec_p = Path(tmp) / "child.json"
            child_gif_p = Path(tmp) / "child.gif"

            base_spec = {
                "width": 64,
                "height": 64,
                "palette": "cozy24",
                "defs": {
                    "axe": {
                        "width": 8,
                        "height": 8,
                        "ops": [{"op": "rect", "x": 3, "y": 0, "w": 2, "h": 8, "color": "wood"}],
                    }
                },
                "ops": [
                    {"op": "char_rig", "x": 0, "y": 0, "size": 64, "dir": "down", "pose": "work", "frame": 2, "hat": "wheat"},
                ],
            }
            base_spec_p.write_text(json.dumps(base_spec), encoding="utf-8")
            self.assertEqual(main(["render", str(base_spec_p), "-o", str(base_png_p)]), 0)
            self.assertEqual(main(["extract", str(base_png_p)]), 0)

            # Child spec extends the generated PNG directly and uses rotated stamp + load_png
            child_spec = {
                "extends": str(base_png_p),
                "frames": [
                    {"name": "f0", "ops": [{"op": "stamp", "def": "axe", "x": 28, "y": 28, "angle": 45, "pivot": [4, 4]}]},
                    {"name": "f1", "ops": [{"op": "load_png", "path": str(base_png_p), "crop": [16, 16, 32, 32], "x": 16, "y": 16}]},
                ],
            }
            child_spec_p.write_text(json.dumps(child_spec), encoding="utf-8")
            self.assertEqual(main(["render", str(child_spec_p), "-o", str(child_gif_p)]), 0)
            self.assertTrue(child_gif_p.exists())

    def test_v07_zbuffer_ellipse_bezier_particles_keyframes_and_layers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            spec_p = Path(tmp) / "v07.json"
            out_gif = Path(tmp) / "v07.gif"
            layers_dir = Path(tmp) / "layers"

            spec = {
                "width": 32,
                "height": 32,
                "palette": "cozy24",
                "layers": [
                    {
                        "name": "ground",
                        "ops": [
                            {"op": "ellipse", "cx": 16, "cy": 26, "rx": 10, "ry": 3, "color": "shadow"},
                            {"op": "bezier", "points": [[4, 24], [16, 8], [28, 24]], "color": "wood", "thickness": 2},
                        ],
                    },
                    {
                        "name": "z_test",
                        "ops": [
                            {"op": "rect", "x": 12, "y": 12, "w": 8, "h": 8, "color": "roof", "z": 10},
                            {"op": "rect", "x": 12, "y": 12, "w": 8, "h": 8, "color": "water", "z": 5},
                        ],
                    },
                ],
                "keyframes": [
                    {
                        "name": "start",
                        "steps": 3,
                        "ops": [
                            {"op": "rect", "x": 2, "y": 2, "w": 4, "h": 4, "color": "wheat"},
                            {"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 6, "color": "cream", "mode": "smoke"},
                        ],
                    },
                    {
                        "name": "end",
                        "steps": 1,
                        "ops": [
                            {"op": "rect", "x": 14, "y": 2, "w": 4, "h": 4, "color": "wheat"},
                            {"op": "particles", "x": 0, "y": 0, "w": 32, "h": 32, "count": 6, "color": "cream", "mode": "smoke"},
                        ],
                    },
                ],
            }
            frames, names = run_frames(spec)
            # 3 interpolated frames from 'start' + 1 final 'end' frame = 4 frames
            self.assertEqual(len(frames), 4)
            self.assertEqual(names[0], "start_0")
            # Z-buffer: 'roof' (z=10) at (15,15) must NOT be overwritten by 'water' (z=5)
            self.assertEqual(frames[0].get_pixel(15, 15), (194, 75, 56, 255))

            spec_p.write_text(json.dumps(spec), encoding="utf-8")
            self.assertEqual(
                main(["render", str(spec_p), "-o", str(out_gif), "--layers-dir", str(layers_dir)]),
                0,
            )
            self.assertTrue(out_gif.exists())
            self.assertTrue((layers_dir / "00_ground.png").exists())
            self.assertTrue((layers_dir / "01_z_test.png").exists())


if __name__ == "__main__":
    unittest.main()

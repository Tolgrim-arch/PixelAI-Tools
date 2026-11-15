import json
from pathlib import Path
import unittest

from pixelai.canvas import Canvas
from pixelai.inspect_tool import analyze_canvas
from pixelai.portrait import draw_field_farmer
from pixelai.portrait_mistria import draw_mistria_portrait
from pixelai.runner import run_spec


ROOT = Path(__file__).resolve().parent.parent


class FieldFarmerTest(unittest.TestCase):
    def render(self, **options):
        canvas = Canvas(116, 144)
        draw_field_farmer(canvas, 0, 0, {}, options)
        return canvas

    def test_left_is_exact_raster_mirror(self):
        right = self.render()
        left = self.render(face_dir="three_quarter_left")
        for y in range(right.height):
            self.assertEqual(
                [right.get_pixel(x, y) for x in reversed(range(right.width))],
                [left.get_pixel(x, y) for x in range(left.width)],
            )

    def test_hat_and_expression_change_separate_regions(self):
        default = self.render()
        bare = self.render(hat=False)
        neutral = self.render(expression="neutral")
        self.assertNotEqual(default.get_pixel(41, 13), bare.get_pixel(41, 13))
        self.assertEqual(default.get_pixel(41, 13), neutral.get_pixel(41, 13))
        self.assertNotEqual(default.get_pixel(55, 65), neutral.get_pixel(55, 65))
        self.assertEqual(default.get_pixel(55, 65), bare.get_pixel(55, 65))


class MistriaPortraitTest(unittest.TestCase):
    def render_mistria(self, **options):
        canvas = Canvas(122, 161)
        draw_mistria_portrait(canvas, 1, 1, {}, options)
        return canvas

    def test_samurai_and_farmer_specs_are_single_connected_sprites(self):
        expected = [
            (
                "samurai",
                122,
                161,
                {
                    "width": 122,
                    "height": 161,
                    "palette": "mistria_portrait",
                    "ops": [{"op": "portrait_rig", "preset": "samurai", "scar": True, "hat_mode": "back"}],
                },
            ),
            (
                "farmer",
                146,
                161,
                {
                    "width": 146,
                    "height": 161,
                    "palette": "mistria_portrait",
                    "ops": [{"op": "portrait_rig", "preset": "farmer", "hat": True, "beard": True, "gesture": "wave"}],
                },
            ),
        ]
        for label, w, h, spec in expected:
            canvas = run_spec(spec)
            stats = analyze_canvas(canvas)
            self.assertEqual((canvas.width, canvas.height), (w, h), label)
            self.assertEqual(stats["islands"], 1, label)
            self.assertGreaterEqual(stats["unique_colors"], 18, label)

    def test_samurai_face_dir_hat_and_scar_options(self):
        right = self.render_mistria(preset="samurai", face_dir="three_quarter_right", hat=False, scar=True)
        left = self.render_mistria(preset="samurai", face_dir="three_quarter_left", hat=False, scar=True)
        worn_hat = self.render_mistria(preset="samurai", hat=True, hat_mode="worn", scar=True)
        no_scar = self.render_mistria(preset="samurai", hat=False, scar=False)

        self.assertEqual(analyze_canvas(right)["islands"], 1)
        self.assertEqual(analyze_canvas(left)["islands"], 1)
        self.assertNotEqual(right.get_pixel(46, 62), no_scar.get_pixel(46, 62))
        self.assertNotEqual(right.get_pixel(59, 14), worn_hat.get_pixel(59, 14))
        self.assertNotEqual(right.get_pixel(57, 21), left.get_pixel(57, 21))

    def test_farmer_presets_and_wave_gesture(self):
        waving = self.render_mistria(preset="farmer", hat=True, beard=True, gesture="wave")
        idle = self.render_mistria(preset="farmer", hat=False, beard=False, gesture="idle")
        self.assertEqual(analyze_canvas(waving)["islands"], 1)
        self.assertEqual(analyze_canvas(idle)["islands"], 1)
        self.assertNotEqual(waving.get_pixel(102, 70), idle.get_pixel(102, 70))
        self.assertNotEqual(waving.get_pixel(44, 18), idle.get_pixel(44, 18))


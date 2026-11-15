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
        self.assertNotEqual(default.get_pixel(58, 10), bare.get_pixel(58, 10))
        self.assertEqual(default.get_pixel(58, 10), neutral.get_pixel(58, 10))
        self.assertNotEqual(default.get_pixel(65, 74), neutral.get_pixel(65, 74))
        self.assertEqual(default.get_pixel(65, 74), bare.get_pixel(65, 74))


class MistriaPortraitTest(unittest.TestCase):
    def render_mistria(self, **options):
        canvas = Canvas(122, 161)
        draw_mistria_portrait(canvas, 1, 1, {}, options)
        return canvas

    def test_samurai_and_farmer_specs_are_single_connected_sprites(self):
        expected = [
            ("samurai_portrait.json", 122, 161),
            ("portrait_farmer_rig.json", 146, 161),
        ]
        for filename, w, h in expected:
            spec = json.loads((ROOT / filename).read_text(encoding="utf-8"))
            canvas = run_spec(spec)
            stats = analyze_canvas(canvas)
            self.assertEqual((canvas.width, canvas.height), (w, h), filename)
            self.assertEqual(stats["islands"], 1, filename)
            self.assertGreaterEqual(stats["unique_colors"], 18, filename)

    def test_samurai_face_dir_hat_and_scar_options(self):
        right = self.render_mistria(preset="samurai", face_dir="three_quarter_right", hat=False, scar=True)
        left = self.render_mistria(preset="samurai", face_dir="three_quarter_left", hat=False, scar=True)
        worn_hat = self.render_mistria(preset="samurai", hat=True, hat_mode="worn", scar=True)
        no_scar = self.render_mistria(preset="samurai", hat=False, scar=False)

        self.assertEqual(analyze_canvas(right)["islands"], 1)
        self.assertEqual(analyze_canvas(left)["islands"], 1)
        self.assertNotEqual(right.get_pixel(71, 40), no_scar.get_pixel(71, 40))
        self.assertNotEqual(right.get_pixel(25, 24), worn_hat.get_pixel(25, 24))
        self.assertNotEqual(right.get_pixel(11, 99), left.get_pixel(11, 99))

    def test_farmer_presets_and_wave_gesture(self):
        waving = self.render_mistria(preset="farmer", hat=True, beard=True, gesture="wave")
        idle = self.render_mistria(preset="farmer", hat=False, beard=False, gesture="idle")
        self.assertEqual(analyze_canvas(waving)["islands"], 1)
        self.assertEqual(analyze_canvas(idle)["islands"], 1)
        self.assertNotEqual(waving.get_pixel(110, 56), idle.get_pixel(110, 56))
        self.assertNotEqual(waving.get_pixel(59, 10), idle.get_pixel(59, 10))


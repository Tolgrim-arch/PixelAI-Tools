import unittest

from pixelai.building import draw_building
from pixelai.canvas import Canvas
from pixelai.ui import draw_ui_rig


class UIQualityTest(unittest.TestCase):
    def test_large_panel_preserves_native_corner_and_border_thickness(self):
        small, large = Canvas(48, 32), Canvas(320, 160)
        for canvas in (small, large):
            draw_ui_rig(canvas, 0, 0, {}, {"w": canvas.width, "h": canvas.height})
        for y in range(6):
            for x in range(6):
                self.assertEqual(small.get_pixel(x, y), large.get_pixel(x, y))
        self.assertEqual(small.get_pixel(4, 4), large.get_pixel(160, 80))

    def test_frame_only_has_transparent_center(self):
        canvas = Canvas(80, 48)
        draw_ui_rig(canvas, 0, 0, {}, {"w": 80, "h": 48, "inner_fill": False})
        self.assertEqual(canvas.get_pixel(40, 24)[3], 0)
        self.assertEqual(canvas.get_pixel(1, 24)[3], 255)

    def test_invalid_component_is_not_silent_blank_output(self):
        with self.assertRaisesRegex(ValueError, "Unknown UI kind"):
            draw_ui_rig(Canvas(32, 32), 0, 0, {}, {"kind": "dialogue_typo"})

    def test_material_decoration_stays_outside_transparent_content(self):
        for theme in ("wood", "stone", "gold", "paper", "dark"):
            with self.subTest(theme=theme):
                canvas = Canvas(160, 80)
                draw_ui_rig(canvas, 0, 0, {}, {"w": 160, "h": 80, "theme": theme,
                                              "frame_width": 8, "inner_fill": False})
                self.assertEqual(canvas.get_pixel(0, 0)[3], 0)
                self.assertTrue(all(canvas.get_pixel(x, y)[3] == 0
                                    for y in range(8, 72) for x in range(8, 152)))
                self.assertEqual(canvas.clipped_pixels, 0)
                self.assertGreater(len(set(canvas.pixels)), 4)

    def test_frame_width_rejects_out_of_range_or_no_content(self):
        for frame, size in ((2, 32), (13, 32), (8, 16)):
            with self.assertRaisesRegex(ValueError, "frame_width"):
                draw_ui_rig(Canvas(size, size), 0, 0, {},
                            {"w": size, "h": size, "frame_width": frame})


class BuildingShadowQualityTest(unittest.TestCase):
    def render(self, **options):
        canvas = Canvas(160, 160)
        draw_building(canvas, {}, {"x": 20, "y": 24, "w": 96, "h": 100,
                                   "chimney": False, **options})
        return canvas

    def test_shadow_is_translucent_straight_footprint_excluded_from_outline(self):
        canvas = self.render()
        self.assertTrue(canvas.shadow_pixels)
        self.assertTrue(canvas.shadow_pixels <= canvas.no_outline)
        self.assertTrue(all(canvas.pixels[i][3] == 56 for i in canvas.shadow_pixels))
        bottom_y = max(i // canvas.width for i in canvas.shadow_pixels)
        bottom = [i % canvas.width for i in canvas.shadow_pixels if i // canvas.width == bottom_y]
        self.assertGreater(max(bottom) - min(bottom), 70)

    def test_shadow_can_be_disabled_and_custom_opacity_is_honored(self):
        self.assertFalse(self.render(ground_shadow=False).shadow_pixels)
        custom = self.render(shadow_opacity=0.1)
        self.assertTrue(all(custom.pixels[i][3] == 26 for i in custom.shadow_pixels))

    def test_invalid_opacity_restores_canvas_flags(self):
        canvas = Canvas(160, 160)
        with self.assertRaisesRegex(ValueError, "shadow_opacity"):
            draw_building(canvas, {}, {"shadow_opacity": 2})
        self.assertFalse(canvas.mark_shadow)
        self.assertFalse(canvas.mark_no_outline)


if __name__ == "__main__":
    unittest.main()

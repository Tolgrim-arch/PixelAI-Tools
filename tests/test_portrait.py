import unittest

from pixelai.canvas import Canvas
from pixelai.portrait import draw_field_farmer


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

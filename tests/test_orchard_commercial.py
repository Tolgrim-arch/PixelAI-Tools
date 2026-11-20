import unittest

from pixelai.canvas import Canvas
from pixelai.nature import draw_nature_rig


class OrchardCommercialTests(unittest.TestCase):
    def render(self, seed=41, **op):
        canvas = Canvas(64, 78)
        draw_nature_rig(canvas, 0, 0, {}, {
            "kind": "tree", "variant": "fruit", "seed": seed, "shadow": False,
            "accent_color": "#dd9441", **op,
        })
        return canvas

    def test_seed_changes_lower_trunk_silhouette_at_fixed_foot_height(self):
        first = self.render(41)
        second = self.render(92)
        first_trunk = self.lower_shape(first)
        second_trunk = self.lower_shape(second)
        self.assertEqual(max(y for _, y in first_trunk), max(y for _, y in second_trunk))
        self.assertGreater(len(first_trunk ^ second_trunk), 40)
        self.assertEqual(first.pixels, self.render(41).pixels)

    def test_apples_and_pears_change_fruit_shape_without_changing_tree(self):
        apple = self.render(fruit="apple")
        pear = self.render(fruit="pear")
        self.assertEqual(self.render().pixels, apple.pixels)
        self.assertEqual([p[3] for p in apple.pixels], [p[3] for p in pear.pixels])
        apple_pixels = self.fruit_pixels(apple)
        pear_pixels = self.fruit_pixels(pear)
        self.assertGreater(len(apple_pixels ^ pear_pixels), 20)
        self.assertGreaterEqual(len(apple_pixels), 40)
        self.assertGreaterEqual(len(pear_pixels), 40)

    def test_unknown_fruit_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, "Unknown tree fruit"):
            self.render(fruit="plum")

    @staticmethod
    def lower_shape(canvas):
        return {(i % canvas.width, i // canvas.width) for i, pixel in enumerate(canvas.pixels)
                if i // canvas.width >= 55 and pixel[3] == 255}

    @staticmethod
    def fruit_pixels(canvas):
        return {i for i, (r, g, b, a) in enumerate(canvas.pixels)
                if r > 120 and r > g > b and a == 255}

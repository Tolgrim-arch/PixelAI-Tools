import unittest

from pixelai.canvas import Canvas
from pixelai.nature import draw_nature_rig


class NatureCommercialTests(unittest.TestCase):
    def rock(self, variant="mossy", seed=25, **options):
        canvas = Canvas(60, 46)
        draw_nature_rig(canvas, 2, 2, {}, {
            "kind": "rock", "variant": variant, "seed": seed,
            "w": 56, "h": 42, "color": "#7b8297", **options,
        })
        return canvas

    def tree(self, **options):
        canvas = Canvas(64, 78)
        draw_nature_rig(canvas, 0, 0, {}, {
            "kind": "tree", "variant": "fruit", "seed": 41, **options,
        })
        return canvas

    def test_rock_seed_changes_shape_deterministically(self):
        for variant in ("boulder", "mossy", "ore"):
            with self.subTest(variant=variant):
                first = self.rock(variant)
                second = self.rock(variant, seed=96)
                self.assertEqual(first.pixels, self.rock(variant).pixels)
                self.assertNotEqual(self.opaque_mask(first), self.opaque_mask(second))

    def test_moss_has_an_independent_palette_and_stays_inside_the_rock(self):
        normal = self.rock()
        tinted = self.rock(foliage_color="#a34c8e")
        self.assertIn((88, 156, 76, 255), normal.pixels)
        self.assertIn((163, 76, 142, 255), tinted.pixels)
        self.assertNotIn((88, 156, 76, 255), tinted.pixels)
        self.assertIn((123, 130, 151, 255), normal.pixels)
        self.assertIn((123, 130, 151, 255), tinted.pixels)
        self.assertEqual(self.opaque_mask(normal), self.opaque_mask(tinted))
        self.assertEqual(normal.shadow_pixels, tinted.shadow_pixels)

    def test_ore_deposit_has_connected_facets_inside_the_boulder(self):
        ore = self.rock("ore", seed=96, accent_color="#d69d57")
        stone = self.rock("boulder", seed=96)
        self.assertEqual(self.opaque_mask(ore), self.opaque_mask(stone))
        deposit = {(i % ore.width, i // ore.width) for i, (r, g, b, a) in enumerate(ore.pixels)
                   if r > g > b and a == 255}
        self.assertGreaterEqual(len(deposit), 18)
        self.assertGreaterEqual(len({ore.get_pixel(*point) for point in deposit}), 3)
        pending = [next(iter(deposit))]
        connected = set(pending)
        while pending:
            x, y = pending.pop()
            for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if point in deposit - connected:
                    pending.append(point)
                    connected.add(point)
        self.assertEqual(deposit, connected)

    def test_broadleaf_color_preserves_crown_shape(self):
        green = self.tree(color="#58905b")
        purple = self.tree(color="#c02dcc")
        self.assertIn((88, 144, 91, 255), green.pixels)
        self.assertIn((192, 45, 204, 255), purple.pixels)
        self.assertNotEqual(green.pixels, purple.pixels)
        self.assertEqual(self.opaque_mask(green), self.opaque_mask(purple))

    def test_broadleaf_band_colors_and_ramp_override_base_color(self):
        bands = ["#aabcde", "#8098ad", "#627684", "#475765"]
        ramp = list(reversed(bands))
        old = self.tree(band_colors=bands)
        self.assertEqual(old.pixels, self.tree(band_colors=bands, color="#c02dcc").pixels)
        self.assertEqual(old.pixels, self.tree(ramp=ramp, color="#c02dcc").pixels)
        self.assertEqual(old.pixels, self.tree(band_colors=bands, ramp=list(bands)).pixels)

    @staticmethod
    def opaque_mask(canvas):
        return [pixel[3] == 255 for pixel in canvas.pixels]

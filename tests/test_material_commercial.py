import unittest

from pixelai.materials import MATERIALS
from pixelai.runner import run_frames


def render(*ops, width=64, height=48):
    frames, _ = run_frames({"width": width, "height": height, "style": "lineless", "ops": list(ops)})
    return frames[0]


class MaterialSurfaceTest(unittest.TestCase):
    def test_seed_changes_geometry_and_each_material_uses_unique_shapes(self):
        ramp = ["#595059", "#706373", "#867887", "#9f91a0", "#b8a9b6"]
        structures = set()
        for kind in MATERIALS:
            with self.subTest(kind=kind):
                op = {"op": "material", "kind": kind, "colors": ramp, "seed": 17}
                pixels = render(op).pixels
                self.assertEqual(pixels, render(op).pixels)
                variant = render({**op, "seed": 57}).pixels
                self.assertGreater(sum(a != b for a, b in zip(pixels, variant)), 100)
                self.assertGreaterEqual(len(set(pixels)), 4)
                self.assertTrue(all(pixel[3] == 255 for pixel in pixels))
                structures.add(tuple(pixels))
        self.assertEqual(len(structures), len(MATERIALS))

    def test_inside_preserves_an_irregular_alpha_mask_and_shadow(self):
        shadow = {"op": "ellipse", "cx": 20, "cy": 26, "rx": 8, "ry": 2,
                  "color": "#28313d30", "shadow": True}
        silhouette = {"op": "polygon", "points": [[7, 5], [25, 7], [30, 17], [22, 25], [11, 21], [4, 14]],
                      "color": "#846349c0"}
        original = render(shadow, silhouette)
        painted = render(shadow, silhouette, {"op": "material", "kind": "trunk", "inside": True})
        self.assertEqual([pixel[3] for pixel in original.pixels], [pixel[3] for pixel in painted.pixels])
        self.assertEqual(original.shadow_pixels, painted.shadow_pixels)
        for i in original.shadow_pixels:
            self.assertEqual(original.pixels[i], painted.pixels[i])
        self.assertNotEqual(painted.get_pixel(16, 14), original.get_pixel(16, 14))

    def test_small_offset_material_stays_in_its_rectangle(self):
        for kind in MATERIALS:
            with self.subTest(kind=kind):
                canvas = render({"op": "material", "kind": kind, "x": 3, "y": 2, "w": 9, "h": 6},
                                width=16, height=12)
                self.assertEqual(sum(pixel[3] > 0 for pixel in canvas.pixels), 54)
                self.assertEqual(canvas.get_pixel(2, 2)[3], 0)
                self.assertEqual(canvas.get_pixel(11, 7)[3], 255)

    def test_soil_and_cloth_keep_material_structure_at_native_and_three_x(self):
        for kind in ("soil", "cloth"):
            with self.subTest(kind=kind):
                native = render({"op": "material", "kind": kind, "seed": 23})
                zoomed = render({"op": "material", "kind": kind, "seed": 23},
                                width=192, height=144)
                self.assertGreaterEqual(len(set(native.pixels)), 5)
                self.assertGreaterEqual(len(set(zoomed.pixels)), 5)
                self.assertEqual(native.get_pixel(0, 0)[3], 255)
                self.assertEqual(zoomed.get_pixel(191, 143)[3], 255)

    def test_rejects_invalid_material_parameters(self):
        for fields, error in (({"kind": "unknown"}, "Unknown material"),
                              ({"inside": 1}, "inside must be a boolean"),
                              ({"w": 0}, "positive integers"),
                              ({"colors": []}, "five colors"),
                              ({"color": "transparent"}, "nonzero alpha")):
            with self.subTest(fields=fields):
                with self.assertRaisesRegex(ValueError, error):
                    render({"op": "material", "kind": "rock", **fields})

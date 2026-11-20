import unittest

from pixelai.building import draw_building
from pixelai.canvas import Canvas
from pixelai.color import darken, parse_color
from pixelai.filters import pad, scale


class BuildingProjectionTest(unittest.TestCase):
    def render(self, **options):
        canvas = Canvas(128, 120)
        draw_building(canvas, {}, {"x": 10, "y": 14, "w": 100, "h": 90, "roof_h": 40,
                                   "depth": 24, "wall_color": "#dac49a", "chimney": False,
                                   "ground_shadow": False, **options})
        return canvas

    def test_wall_and_foundation_project_into_the_return(self):
        canvas = self.render(windows=False)
        wall = parse_color("#dac49a")
        self.assertEqual(canvas.get_pixel(74, 80), wall)
        self.assertEqual(canvas.get_pixel(96, 80), darken(wall, .79))
        self.assertEqual(canvas.get_pixel(74, 103)[3], 255)
        self.assertEqual(canvas.get_pixel(96, 103)[3], 0)
        self.assertEqual(canvas.clipped_pixels, 0)

    def test_cross_gable_joins_roof_with_a_filled_return(self):
        plain = self.render(dormer=False)
        gabled = self.render(dormer=True)
        wall = parse_color("#dac49a")
        self.assertTrue(any(gabled.get_pixel(x, y) == wall and plain.get_pixel(x, y) != wall
                            for y in range(28, 54) for x in range(23, 55)))
        self.assertTrue(any(gabled.get_pixel(x, y) != plain.get_pixel(x, y)
                            for y in range(18, 26) for x in range(29, 51)))

    def test_roof_courses_are_seeded_and_repeatable(self):
        for style in ("gable", "pitched", "barn"):
            with self.subTest(style=style):
                first = self.render(roof_style=style, seed=88)
                repeat = self.render(roof_style=style, seed=88)
                second = self.render(roof_style=style, seed=93)
                self.assertEqual(first.pixels, repeat.pixels)
                self.assertGreater(sum(a != b for a, b in zip(first.pixels, second.pixels)), 90)
                self.assertEqual(first.clipped_pixels, 0)

    def test_runtime_metadata_describes_placement_and_collision(self):
        canvas = self.render(name="farmhouse_runtime")
        self.assertEqual(len(canvas.attachments), 1)
        attachment = canvas.attachments[0]
        self.assertEqual(attachment["type"], "building")
        self.assertEqual(attachment["name"], "farmhouse_runtime")
        self.assertEqual(attachment["origin"], attachment["y_sort"])
        self.assertEqual(attachment["collision"]["shape"], "polygon")
        self.assertGreaterEqual(len(attachment["collision"]["points"]), 4)
        for point in attachment["collision"]["points"] + [attachment["origin"], attachment["entrance"]]:
            self.assertTrue(0 <= point[0] < canvas.width)
            self.assertTrue(0 <= point[1] < canvas.height)

    def test_runtime_metadata_tracks_padding_and_integer_scale(self):
        canvas = self.render()
        original = canvas.attachments[0]["origin"]
        transformed = scale(pad(canvas, 2), 3)
        self.assertEqual(transformed.attachments[0]["origin"], [(original[0] + 2) * 3,
                                                                (original[1] + 2) * 3])

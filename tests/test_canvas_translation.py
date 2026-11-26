"""Integer translation must preserve polygon coverage, including half ties."""

import unittest

from pixelai.canvas import Canvas


class PolygonTranslationTest(unittest.TestCase):
    def test_integer_translation_does_not_change_polygon_coverage(self):
        points = [(2, 1), (7, 5), (2, 8), (1, 4)]
        first, second = Canvas(32, 32), Canvas(32, 32)
        color = (100, 150, 200, 255)
        first.draw_polygon(points, color)
        second.draw_polygon([(x+7, y+5) for x, y in points], color)
        a = {(i % 32, i // 32) for i, pixel in enumerate(first.pixels) if pixel[3]}
        b = {(i % 32-7, i // 32-5) for i, pixel in enumerate(second.pixels) if pixel[3]}
        self.assertEqual(a, b)

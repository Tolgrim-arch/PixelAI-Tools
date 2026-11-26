"""Functional-region checks distinguish penetration from intentional contact."""

import unittest

from pixelai.geometry import overlap, swept_overlap, validate_polygon, world_regions


class GeometryTest(unittest.TestCase):
    def test_sweep_detects_thin_obstacles_without_blocking_boundary_contact(self):
        moving = [[0, 0], [.1, 0], [.1, 1], [0, 1]]
        needle = [[.5, 0], [.6, 0], [.6, 1], [.5, 1]]
        self.assertFalse(overlap(moving, needle))
        self.assertTrue(swept_overlap(moving, needle, [1, 0]))
        self.assertFalse(swept_overlap(moving, needle, [.4, 0]))
        touching = [[.4, 0], [.5, 0], [.5, 1], [.4, 1]]
        self.assertFalse(swept_overlap(touching, needle, [-1, 0]))

    def test_overlap_contact_and_containment(self):
        a = validate_polygon([[0, 0], [4, 0], [4, 4], [0, 4]])
        self.assertTrue(overlap(a, [[1, 1], [2, 1], [2, 2], [1, 2]]))
        self.assertTrue(overlap(a, [[3, 0], [5, 0], [5, 4], [3, 4]]))
        self.assertFalse(overlap(a, [[4, 0], [8, 0], [8, 4], [4, 4]]))
        self.assertFalse(overlap(a, [[10, 0], [14, 0], [14, 4], [10, 4]]))
        frame = {"regions": [{"id": "feet", "role": "collision", "polygon": a}]}
        self.assertEqual(world_regions(frame, (5, 7))[0]["polygon"][0], [5, 7])
        self.assertEqual(a[0], [0, 0])

    def test_malformed_geometry_is_rejected(self):
        for polygon in ([[0, 0], [1, 1], [2, 2]], [[0, 0], [4, 0], [2, 1], [4, 4], [0, 4]],
                        [[0, 0], [4, 4], [0, 4], [4, 0]], [[0, 0], [0, 0], [4, 4]],
                        [[0, 0], [4, 0], [float("nan"), 4]]):
            with self.assertRaises(ValueError):
                validate_polygon(polygon)

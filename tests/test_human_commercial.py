"""Geometry regressions for native top-down human sprites."""

import unittest

from pixelai.color import parse_color
from pixelai.runner import run_spec


DIRECTIONS = ("down", "up", "left", "right")


def human(size, direction="down", pose="idle", frame=0, **appearance):
    return run_spec({
        "width": size,
        "height": size,
        "palette": "cozy24",
        "style": "lineless",
        "ops": [{
            "op": "char_rig", "size": size, "dir": direction, "pose": pose,
            "frame": frame, "shadow": False, **appearance,
        }],
    })


def footprint(canvas):
    return {
        (x, y) for y in range(canvas.height) for x in range(canvas.width)
        if canvas.get_pixel(x, y)[3]
    }


def neighboring_pixels(x, y):
    return {(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)}


class TopDownHumanTests(unittest.TestCase):
    def test_costumes_and_hair_change_geometry(self):
        for size in (32, 64):
            for direction in DIRECTIONS:
                with self.subTest(size=size, direction=direction):
                    standard = footprint(human(size, direction, outfit="overalls", hair_style="crop"))
                    coat = footprint(human(size, direction, outfit="coat", hair_style="crop"))
                    apron = footprint(human(size, direction, outfit="apron", hair_style="crop"))
                    ponytail = footprint(human(size, direction, outfit="overalls", hair_style="ponytail"))
                    self.assertEqual(len({frozenset(shape) for shape in (standard, coat, apron, ponytail)}), 4)
                    self.assertGreater(len(ponytail - standard), 2)

    def test_tool_is_visible_gripped_and_inside_outline_clearance(self):
        tool = "#b5bfd1"
        handle = "#aa7029"
        skin = "#e2aa81"
        for size in (32, 64):
            for direction in DIRECTIONS:
                for frame in range(4):
                    with self.subTest(size=size, direction=direction, frame=frame):
                        canvas = human(size, direction, "work", frame, outfit="coat",
                                       hair_style="ponytail", tool=tool, handle=handle, skin=skin)
                        solid = footprint(canvas)
                        self.assertEqual(canvas.clipped_pixels, 0)
                        self.assertTrue(all(0 < min(x, y) and max(x, y) < size - 1 for x, y in solid))
                        self.assertGreaterEqual(canvas.pixels.count(parse_color(tool, {})), 2)
                        shaft = {point for point in solid if canvas.get_pixel(*point) == parse_color(handle, {})}
                        self.assertTrue(any(canvas.get_pixel(*neighbor) == parse_color(skin, {})
                                            for point in shaft for neighbor in neighboring_pixels(*point)))
                        pending = [solid.pop()]
                        while pending:
                            connections = neighboring_pixels(*pending.pop()) & solid
                            pending.extend(connections)
                            solid.difference_update(connections)
                        self.assertFalse(solid, "Tool and character must form one connected silhouette")

    def test_walk_has_four_phases_and_reaches_floor(self):
        for size in (32, 64):
            for direction in DIRECTIONS:
                with self.subTest(size=size, direction=direction):
                    frames = [footprint(human(size, direction, "walk", frame)) for frame in range(4)]
                    self.assertEqual(len({frozenset(shape) for shape in frames}), 4)
                    self.assertEqual(len({max(y for _, y in shape) for shape in frames}), 1)

    def test_side_profiles_face_opposite_directions(self):
        for size in (32, 64):
            for pose in ("idle", "walk", "work"):
                with self.subTest(size=size, pose=pose):
                    left = footprint(human(size, "left", pose, hair_style="ponytail"))
                    right = footprint(human(size, "right", pose, hair_style="ponytail"))
                    self.assertNotEqual(left, right)
                    mirrored = {(size - 1 - x, y) for x, y in right}
                    self.assertLess(len(left ^ mirrored) / len(left | mirrored), .03)

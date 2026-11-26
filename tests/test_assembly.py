"""Semantic part changes propagate to children and exported attachments."""

import unittest

from pixelai.assembly import resolve_parts
from pixelai.runner import run_spec


def part(name, offset, parent=None):
    return {"id": name, "offset": offset, "parent": parent, "width": 4, "height": 4,
            "ops": [{"op": "rect", "x": 0, "y": 0, "w": 2, "h": 2, "color": "#448855"}]}


class AssemblyTest(unittest.TestCase):
    def test_parent_origin_and_post_transforms(self):
        parts = [part("body", [3, 4]), part("arm", [4, 0], "body")]
        spec = {"width": 16, "height": 16, "style": "lineless", "ops": [{"op": "assembly", "parts": parts}],
                "post": [{"op": "pad", "size": 1}, {"op": "scale", "factor": 2}]}
        canvas = run_spec(spec)
        self.assertEqual(canvas.get_pixel(16, 10), (68, 136, 85, 255))
        self.assertEqual(canvas.attachments[1]["name"], "arm")
        self.assertEqual(canvas.attachments[1]["origin"], [16, 10])
        parts[0]["offset"] = [4, 5]
        self.assertEqual(resolve_parts(parts)[1][1], (8, 5))

    def test_missing_parent_cycle_and_unknown_parameter(self):
        for parts in ([part("arm", [0, 0], "missing")],
                      [part("a", [0, 0], "b"), part("b", [0, 0], "a")],
                      [{**part("a", [0, 0]), "anatomy_typo": "wide"}]):
            with self.assertRaises(ValueError):
                resolve_parts(parts)

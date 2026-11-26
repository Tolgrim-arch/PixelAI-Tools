"""Body plans change proportions and preserve ground, direction and rigid tools."""

import unittest

from pixelai.canvas import Canvas
from pixelai.human import Human
from pixelai.morphology import BODY_PLANS, Morphology
from pixelai.runner import run_spec
from pixelai.structure import compare_growth


def render(plan, direction="down", pose="idle", frame=0, size=64):
    return run_spec({"width": size, "height": size, "style": "ext_outline", "ops": [
        {"op": "char_rig", "size": size, "dir": direction, "pose": pose, "frame": frame,
         "shadow": False, "morphology": {"body_plan": plan}}]})


class MorphologyTest(unittest.TestCase):
    def test_direction_action_frame_matrix_preserves_outline_clearance(self):
        for size in (32, 64):
            for plan in BODY_PLANS:
                for direction in ("down", "up", "left", "right"):
                    for pose in ("idle", "walk", "attack"):
                        for frame in range(4):
                            with self.subTest(size=size, plan=plan, direction=direction, pose=pose, frame=frame):
                                canvas = render(plan, direction, pose, frame, size)
                                self.assertEqual(canvas.clipped_pixels, 0)
                                self.assertEqual(canvas.warnings, [])
                                self.assertEqual(canvas.attachments[0]["ground_anchor"], [size//2, round(28*size/32)])

    def test_proportion_mapping_is_invertible(self):
        for plan in BODY_PLANS:
            morphology = Morphology({"body_plan": plan})
            for point in ((10, 2), (20, 9), (23, 18), (14, 25), (16, 30)):
                actual = morphology.inverse_point(morphology.point(point))
                self.assertAlmostEqual(actual[0], point[0])
                self.assertAlmostEqual(actual[1], point[1])

    def test_body_plans_change_silhouette_at_fixed_ground(self):
        shapes = set()
        anchor = None
        graphs = []
        for plan in BODY_PLANS:
            canvas = render(plan)
            graph = canvas.attachments[0]
            shapes.add(tuple(pixel[3] for pixel in canvas.pixels))
            if anchor is None:
                anchor = graph["ground_anchor"]
            self.assertEqual(graph["ground_anchor"], anchor)
            self.assertEqual(graph["type"], "anatomy_graph")
            graphs.append(graph)
        self.assertEqual(len(shapes), len(BODY_PLANS))
        self.assertFalse(compare_growth(graphs[1], graphs[2])["normalized_geometry_equal"])

    def test_axe_shape_is_rigid_under_morphology(self):
        def tool(morphology):
            canvas = Canvas(64, 64)
            human = Human(canvas, 0, 0, 64, False, morphology)
            human.axe((140, 90, 40, 255), (190, 210, 220, 255), (15.5, 28), (21.5, 20))
            occupied = [(i % 64, i // 64) for i, pixel in enumerate(canvas.pixels) if pixel[3]]
            left, top = min(x for x, _ in occupied), min(y for _, y in occupied)
            return {(x-left, y-top): canvas.get_pixel(x, y) for x, y in occupied}
        # Integer grip translation makes the exact raster-shape comparison meaningful.
        morphology = Morphology({"body_plan": "stocky"})
        self.assertEqual(tool(None), tool(morphology))

    def test_invalid_and_unsupported_morphology_is_explicit(self):
        for value in ({"body_plan": "unknown"}, {"leg_length": 0}, {"head_width": float("inf")}, {"anatomy_magic": True}):
            with self.assertRaises(ValueError):
                Morphology(value)
        with self.assertRaisesRegex(ValueError, "top-down"):
            render("stocky", size=16)

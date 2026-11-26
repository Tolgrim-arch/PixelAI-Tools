"""Authored body poses change mass placement with fixed ground and rigid tools."""

import unittest

from pixelai.canvas import Canvas
from pixelai.human import Human
from pixelai.morphology import BODY_PLANS, Morphology
from pixelai.posture import PosturedBody
from pixelai.runner import run_spec


class PostureTest(unittest.TestCase):
    def test_invertibility_ground_and_rigid_head_mass(self):
        for plan in BODY_PLANS:
            body = Morphology({"body_plan": plan})
            for lean in (-.15, 0, .15):
                posture = PosturedBody(body, {"lean": lean, "crouch": 1.5})
                for point in ((10, 2), (20, 9), (23, 18), (14, 25), (16, 30)):
                    mapped = posture.point(point)
                    actual = posture.inverse_point(mapped)
                    self.assertAlmostEqual(actual[0], point[0])
                    self.assertAlmostEqual(actual[1], point[1])
                self.assertEqual(posture.point((15.5, 28)), body.point((15.5, 28)))
                first, second = (10, 4), (20, 9)
                self.assertAlmostEqual(posture.point(second)[0]-posture.point(first)[0], body.point(second)[0]-body.point(first)[0])
                self.assertAlmostEqual(posture.point(second)[1]-posture.point(first)[1], body.point(second)[1]-body.point(first)[1])

    def test_direction_action_body_plan_clearance(self):
        for size in (32, 64):
            for plan in BODY_PLANS:
                for direction in ("up", "down", "left", "right"):
                    for pose in ("idle", "walk", "attack"):
                        for lean in (-.15, .15):
                            with self.subTest(size=size, plan=plan, direction=direction, pose=pose, lean=lean):
                                canvas = run_spec({"width": size, "height": size, "style": "ext_outline", "ops": [
                                    {"op": "char_rig", "size": size, "dir": direction, "pose": pose, "frame": 2,
                                     "shadow": False, "morphology": {"body_plan": plan}, "posture": {"lean": lean, "crouch": 1.5}}]})
                                self.assertEqual(canvas.clipped_pixels, 0)
                                self.assertEqual(canvas.warnings, [])
                                self.assertEqual(canvas.attachments[0]["ground_anchor"], [size//2, round(28*size/32)])
                                self.assertEqual(canvas.attachments[0]["posture"], {"lean": lean, "crouch": 1.5})

    def test_tool_raster_is_rigid_and_body_mass_moves(self):
        body = Morphology({})
        posture = PosturedBody(body, {"lean": .15, "crouch": 1.5})
        def tool(mapping):
            canvas = Canvas(64, 64)
            Human(canvas, 0, 0, 64, False, mapping).axe((140, 90, 40, 255), (190, 210, 220, 255), (18, 17), (24, 9))
            points = [(index % 64, index // 64, color) for index, color in enumerate(canvas.pixels) if color[3]]
            left, top = min(point[0] for point in points), min(point[1] for point in points)
            return {(x-left, y-top): color for x, y, color in points}
        self.assertEqual(tool(body), tool(posture))
        self.assertNotEqual(body.point((15.5, 14.6)), posture.point((15.5, 14.6)))
        self.assertEqual(body.point((15.5, 28)), posture.point((15.5, 28)))

    def test_example_loads_body_before_the_tool_moves(self):
        import json
        from pathlib import Path
        from pixelai.runner import run_frames
        spec = json.loads((Path(__file__).resolve().parents[1] / "specs/acting_strike.json").read_text())
        frames, _ = run_frames(spec)
        graphs = [next(record for record in frame.attachments if record.get("type") == "anatomy_graph") for frame in frames]
        first = {node["id"]: node["point"] for node in graphs[0]["nodes"]}
        second = {node["id"]: node["point"] for node in graphs[1]["nodes"]}
        self.assertNotEqual(first["chest"], second["chest"])
        self.assertNotEqual(first["head"], second["head"])
        for foot in ("leg_0_foot", "leg_1_foot"):
            self.assertEqual(first[foot], second[foot])
        self.assertNotEqual(frames[0].pixels, frames[1].pixels)
        from pixelai.motion_analysis import analyze_motion
        motion = analyze_motion(frames, spec["durations_ms"], spec["clips"])
        self.assertTrue(motion["clips"]["strike"]["body_motion_detected"])
        self.assertEqual(motion["clips"]["strike"]["transitions"][0]["ground_delta_px"], 0)

    def test_invalid_and_unsupported_posture(self):
        for value in ({"lean": .16}, {"crouch": -1}, {"lean": True}, {"crouch": float("nan")}, {"magic": 1}):
            with self.assertRaises(ValueError):
                PosturedBody(Morphology({}), value)
        with self.assertRaisesRegex(ValueError, "top-down"):
            run_spec({"width": 16, "height": 16, "ops": [{"op": "char_rig", "size": 16, "posture": {"lean": .1}}]})

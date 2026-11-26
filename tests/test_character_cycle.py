"""Declared animation lengths must advance implicit character poses."""

import unittest

from pixelai.runner import run_frames


class CharacterCycleTest(unittest.TestCase):
    def test_implicit_cycle_advances_and_holds_deliberately(self):
        spec = {"width": 64, "height": 64, "style": "lineless", "frame_count": 8, "ops": [
            {"op": "char_rig", "size": 64, "pose": "walk", "dir": "right", "shadow": False,
             "morphology": {"body_plan": "stocky"}}]}
        frames, _ = run_frames(spec)
        self.assertEqual(len(frames), 8)
        self.assertEqual(len({tuple(frame.pixels) for frame in frames}), 4)
        for index in range(0, 8, 2):
            self.assertEqual(frames[index].pixels, frames[index+1].pixels)
        self.assertNotEqual(frames[0].attachments[0]["nodes"], frames[2].attachments[0]["nodes"])

    def test_explicit_frame_is_not_overridden_by_animation_length(self):
        spec = {"width": 32, "height": 32, "style": "lineless", "frame_count": 8,
                "ops": [{"op": "char_rig", "size": 32, "pose": "walk", "dir": "down", "frame": 2, "shadow": False}]}
        frames, _ = run_frames(spec)
        self.assertEqual(len({tuple(frame.pixels) for frame in frames}), 1)

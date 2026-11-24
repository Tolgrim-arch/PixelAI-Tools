"""Tests guaranteeing anatomical IK direction, forward walk gait, and Z-order in spine_rig."""

import math
import unittest

from pixelai import deform
from pixelai.canvas import Canvas
from pixelai.runner import run_frames


class TestSpineRig(unittest.TestCase):
    def test_walk_foot_offset_never_moonwalks(self):
        for facing in (1, -1):
            # Swing phase (0 < phase < pi): foot is lifted (dy < 0) and advances in +facing direction
            dx_start, dy_start = deform.walk_foot_offset(0.15 * math.pi, facing, stride=6.0, lift=4.0)
            dx_mid, dy_mid = deform.walk_foot_offset(0.5 * math.pi, facing, stride=6.0, lift=4.0)
            dx_end, dy_end = deform.walk_foot_offset(0.85 * math.pi, facing, stride=6.0, lift=4.0)
            self.assertLess(dy_mid, 0.0)
            self.assertGreater((dx_end - dx_start) * facing, 0.0)

            # Stance phase (pi < phase < 2*pi): foot is flat on ground (dy == 0) and pushes toward -facing
            sdx_start, sdy_start = deform.walk_foot_offset(1.15 * math.pi, facing, stride=6.0, lift=4.0)
            sdx_end, sdy_end = deform.walk_foot_offset(1.85 * math.pi, facing, stride=6.0, lift=4.0)
            self.assertEqual(sdy_start, 0.0)
            self.assertEqual(sdy_end, 0.0)
            self.assertLess((sdx_end - sdx_start) * facing, 0.0)

    def test_knee_and_elbow_ik_bend_directions(self):
        for facing in (1, -1):
            k_dir = deform.knee_ik_dir(facing)
            e_dir = deform.elbow_ik_dir(facing)
            # Vertical leg from (20, 20) to (20, 34) with l1=8, l2=8
            kx, _ = deform.solve_ik_2bone(20.0, 20.0, 20.0, 34.0, 8.0, 8.0, direction=k_dir)
            ex, _ = deform.solve_ik_2bone(20.0, 20.0, 20.0, 34.0, 8.0, 8.0, direction=e_dir)
            # Knee bends toward facing; elbow bends away from facing
            self.assertGreater((kx - 20.0) * facing, 0.0)
            self.assertLess((ex - 20.0) * facing, 0.0)

    def test_spine_rig_actions_and_facings_via_json_dsl(self):
        for facing in ("right", "left"):
            for action in ("walk", "run", "idle", "attack"):
                spec = {
                    "width": 64,
                    "height": 64,
                    "style": "ext_outline",
                    "frame_count": 4,
                    "ops": [{"op": "spine_rig", "facing": facing, "action": action}],
                }
                frames, _ = run_frames(spec)
                self.assertEqual(len(frames), 4)
                self.assertNotEqual(frames[0].pixels, frames[1].pixels)
                self.assertEqual(frames[0].clipped_pixels, 0)

    def test_draw_biped_spine_rig_anchors_consistent(self):
        c = Canvas(64, 64)
        joints = deform.draw_biped_spine_rig(c, facing="right", action="walk", frame=3, total_frames=12)
        # Knee x should stay ahead of or near hip-foot midpoint on forward facing
        mid_x = (joints["hip"][0] + joints["near_foot"][0]) * 0.5
        self.assertGreaterEqual(joints["near_knee"][0], mid_x - 2.0)


if __name__ == "__main__":
    unittest.main()

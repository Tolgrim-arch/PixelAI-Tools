"""Reference movement is deterministic, non-tunneling and role-aware."""

import unittest

from pixelai.motion import simulate_motion
from pixelai.runtime import actor_track, frame_at


def actor(name, position, velocity=None, role="collision"):
    source = {"id": name, "position": position, "clip": "idle"}
    if velocity is not None:
        source["velocity"] = velocity
    data = {"frames": [{"id": "0", "duration_ms": 100, "pivot": [2, 4],
                        "regions": [{"id": "body", "role": role, "polygon": [[0, 0], [4, 0], [4, 4], [0, 4]]}]}],
            "clips": {"idle": {"frames": ["0"], "loop": True}}}
    return source, data, actor_track(source, data)


class MotionTest(unittest.TestCase):
    def test_collision_stop_and_screenshot_sampling_independence(self):
        actors = [actor("hero", [10, 10], [100, 0]), actor("wall", [20, 10])]
        sampled, report = simulate_motion(actors, [0, 100, 200], frame_at, "block")
        sparse, _ = simulate_motion(list(reversed(actors)), [200], frame_at, "block")
        self.assertEqual(sampled[200], sparse[200])
        self.assertEqual(sampled[200]["hero"], [16, 10])
        self.assertEqual(report["contacts"][0]["obstacle"], "wall")
        free, _ = simulate_motion(actors, [200], frame_at, "report")
        self.assertEqual(free[200]["hero"], [30, 10])

    def test_fast_movement_and_nonphysical_regions(self):
        actors = [actor("hero", [10, 10], [10000, 0]), actor("wall", [20, 10])]
        positions, _ = simulate_motion(actors, [10], frame_at, "block")
        self.assertEqual(positions[10]["hero"], [16, 10])
        positions, _ = simulate_motion([actor("hero", [10, 10], [10000, 0]), actor("trigger", [20, 10], role="interaction")], [10], frame_at, "block")
        self.assertEqual(positions[10]["hero"], [110, 10])

    def test_invalid_initial_geometry_and_budget_exhaustion(self):
        with self.assertRaisesRegex(ValueError, "overlaps at 0ms"):
            simulate_motion([actor("a", [10, 10]), actor("b", [11, 10])], [0], frame_at, "block")
        with self.assertRaisesRegex(ValueError, "budget exhausted"):
            simulate_motion([actor("a", [10, 10], [100, 0])], [100], frame_at, "block", budget=2)

    def test_timeline_moves_are_swept_and_state_expansion_is_rejected(self):
        source, data, _ = actor("hero", [10, 10])
        source["timeline"] = [{"at_ms": 10, "position": [30, 10]}]
        positions, _ = simulate_motion([(source, data, actor_track(source, data)), actor("wall", [20, 10])], [10], frame_at, "block")
        self.assertEqual(positions[10]["hero"], [16, 10])
        data["frames"].append({**data["frames"][0], "id": "wide", "regions": [
            {"id": "body", "role": "collision", "polygon": [[0, 0], [14, 0], [14, 4], [0, 4]]}]})
        data["clips"]["wide"] = {"frames": ["wide"], "loop": True}
        data["transitions"] = [{"from": "idle", "to": "wide"}]
        source["timeline"] = [{"at_ms": 10, "clip": "wide"}]
        with self.assertRaisesRegex(ValueError, "overlaps at 10ms"):
            simulate_motion([(source, data, actor_track(source, data)), actor("wall", [20, 10])], [10], frame_at, "block")

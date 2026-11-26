"""Plant checks inspect intermediate frames, world movement and bounded input."""

import unittest

from pixelai.contact import assess_contacts, contact_times
from pixelai.runtime import actor_track, frame_at


class ContactTest(unittest.TestCase):
    def setUp(self):
        self.actor = {"id": "hero", "clip": "walk", "position": [10, 20]}
        self.data = {"frames": [
            {"id": str(index), "duration_ms": 10, "pivot": [2, 4], "sockets": {"foot": [2+offset, 4]}}
            for index, offset in enumerate([0, 3, 0])],
            "clips": {"walk": {"frames": ["0", "1", "2"], "loop": True}}}
        self.actors = {"hero": (self.actor, self.data, actor_track(self.actor, self.data))}
        self.window = {"actor": "hero", "socket": "foot", "start_ms": 0, "end_ms": 29}

    def test_hidden_intermediate_drift_and_explicit_tolerance(self):
        self.assertEqual(len(contact_times([self.window], self.actors, 29)), 30)
        report = assess_contacts([self.window], self.actors, frame_at)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["episodes"][0]["max_drift_px"], 3)
        self.assertEqual(report["episodes"][0]["peak_ms"], 10)
        self.window["tolerance_px"] = 3
        self.assertEqual(assess_contacts([self.window], self.actors, frame_at)["status"], "passed")

    def test_world_compensation_and_missing_socket(self):
        positions = {time: {"hero": [10-(3 if 10 <= time < 20 else 0), 20]} for time in range(30)}
        self.assertEqual(assess_contacts([self.window], self.actors, frame_at, positions)["status"], "passed")
        del self.data["frames"][1]["sockets"]["foot"]
        with self.assertRaisesRegex(ValueError, "missing.*10ms"):
            assess_contacts([self.window], self.actors, frame_at)

    def test_invalid_windows_and_budget(self):
        for changes in ({"end_ms": 30}, {"end_ms": 0}, {"tolerance_px": -1}, {"tolerance_px": float("nan")}, {"actor": "missing"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                contact_times([{**self.window, **changes}], self.actors, 29)
        with self.assertRaisesRegex(ValueError, "budget exhausted"):
            contact_times([self.window], self.actors, 29, budget=29)

"""Scores preserve beat timing and exact event occurrences through playback."""

from copy import deepcopy
import unittest

from pixelai.animation_score import score_beats, timeline_events, validate_scores
from pixelai.runtime import actor_track
from pixelai.scenario import assess_scenario


class AnimationScoreTest(unittest.TestCase):
    def setUp(self):
        self.frames = [{"id": str(index), "duration_ms": duration, "sockets": {"tool": [2, 3]}}
                       for index, duration in enumerate([100, 50, 200])]
        self.score = {"schema_version": 1, "intent": "A heavy deliberate strike",
                      "beats": [{"name": name, "purpose": purpose, "start": index, "end": index+1}
                                for index, (name, purpose) in enumerate([("anticipation", "shift weight"), ("impact", "hit target"), ("recovery", "regain balance")])],
                      "events": [{"id": "hit", "name": "damage", "at_ms": 100, "socket": "tool"}]}
        self.clips = {"strike": {"frames": ["0", "1", "2"], "loop": True, "score": self.score},
                      "idle": {"frames": ["0"], "loop": True}}
        self.records = {frame["id"]: frame for frame in self.frames}
        self.data = {"frames": self.frames, "clips": self.clips, "transitions": [{"from": "strike", "to": "idle"}]}
        self.actor = {"id": "hero", "position": [10, 10], "clip": "strike"}

    def events(self, until=1000, budget=10000):
        return timeline_events([(self.actor, self.data, actor_track(self.actor, self.data))], until, budget)

    def test_beats_and_loop_events_include_skipped_screenshots(self):
        validate_scores(self.clips, self.records)
        beats = score_beats(self.clips["strike"], self.records)
        self.assertEqual([(beat["start_ms"], beat["end_ms"]) for beat in beats], [(0, 100), (100, 150), (150, 350)])
        self.assertNotIn("purpose", beats[0])
        self.assertEqual([event["time_ms"] for event in self.events()], [100, 450, 800])
        self.clips["strike"]["loop"] = False
        self.assertEqual([event["time_ms"] for event in self.events()], [100])

    def test_interruptions_restarts_and_position_only_updates(self):
        self.actor["timeline"] = [{"at_ms": 25, "position": [20, 20]}, {"at_ms": 450, "clip": "idle"}]
        self.assertEqual([event["time_ms"] for event in self.events()], [100])
        self.actor["timeline"] = [{"at_ms": 200, "clip": "strike"}]
        self.assertEqual([event["time_ms"] for event in self.events(650)], [100, 300, 650])
        self.actor["timeline"] = [{"at_ms": 0, "clip": "idle"}]
        self.assertEqual(self.events(), [])

    def test_invalid_coverage_socket_and_events(self):
        bad_scores = []
        for field, value in (("schema_version", True), ("intent", ""), ("beats", []), ("events", [{"id": "end", "name": "bad", "at_ms": 350}])):
            bad_scores.append({**deepcopy(self.score), field: value})
        gap = deepcopy(self.score)
        gap["beats"][1]["start"] = 2
        bad_scores.append(gap)
        missing = deepcopy(self.score)
        missing["events"][0]["socket"] = "missing"
        bad_scores.append(missing)
        duplicate = deepcopy(self.score)
        duplicate["events"].append(deepcopy(duplicate["events"][0]))
        bad_scores.append(duplicate)
        for score in bad_scores:
            with self.subTest(score=score), self.assertRaises(ValueError):
                validate_scores({"strike": {**self.clips["strike"], "score": score}}, self.records)
        with self.assertRaisesRegex(ValueError, "budget exhausted"):
            self.events(1000000000, budget=2)

    def test_exact_event_assertion(self):
        trace = [{"time_ms": 100, "actors": [{"actor": "hero"}]}]
        expectation = [{"actor": "hero", "time_ms": 100, "event": "hit"}]
        self.assertEqual(assess_scenario(expectation, trace, events=self.events())["status"], "passed")
        self.assertEqual(assess_scenario(expectation, trace, events=[])["status"], "failed")

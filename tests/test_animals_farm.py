"""Tests for 4-direction farm animal rigs (pig and sheep) and pack generation."""

import unittest

from pixelai.runner import run_frames, run_spec


class TestFarmAnimals(unittest.TestCase):
    def _spec(self, species: str, direction: str = "down", pose: str = "idle", variant: str | None = None):
        op = {"op": "animal_rig", "species": species, "dir": direction, "pose": pose}
        if variant:
            op["variant"] = variant
        return {
            "width": 32,
            "height": 32,
            "palette": "cozy24",
            "style": "ext_outline",
            "style_profile": "cozy_modern",
            "frame_count": 1,
            "ops": [op],
        }

    def test_pig_four_directions_distinct(self):
        views = [
            tuple(run_spec(self._spec("pig", d)).pixels)
            for d in ("down", "up", "left", "right")
        ]
        self.assertEqual(len(set(views)), 4)

    def test_sheep_four_directions_distinct(self):
        views = [
            tuple(run_spec(self._spec("sheep", d)).pixels)
            for d in ("down", "up", "left", "right")
        ]
        self.assertEqual(len(set(views)), 4)

    def test_variants_and_walk_animation(self):
        pink = run_spec(self._spec("pig", "right", "idle", "pink"))
        boar = run_spec(self._spec("pig", "right", "idle", "boar"))
        self.assertNotEqual(pink.pixels, boar.pixels)

        white = run_spec(self._spec("sheep", "right", "idle", "white"))
        black = run_spec(self._spec("sheep", "right", "idle", "black"))
        self.assertNotEqual(white.pixels, black.pixels)

        walk_spec = self._spec("pig", "right", "walk", "pink")
        walk_spec["frame_count"] = 4
        frames, _ = run_frames(walk_spec)
        self.assertEqual(len(frames), 4)
        self.assertGreater(len({tuple(f.pixels) for f in frames}), 1)

    def test_duck_and_rabbit_four_directions_distinct(self):
        for sp in ("duck", "rabbit"):
            views = [
                tuple(run_spec(self._spec(sp, d)).pixels)
                for d in ("down", "up", "left", "right")
            ]
            self.assertEqual(len(set(views)), 4, f"{sp} should have 4 distinct views")

        mallard = run_spec(self._spec("duck", "right", "idle", "mallard"))
        white_duck = run_spec(self._spec("duck", "right", "idle", "white"))
        self.assertNotEqual(mallard.pixels, white_duck.pixels)


if __name__ == "__main__":
    unittest.main()

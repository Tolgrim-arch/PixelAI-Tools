"""Legal neighborhoods and edge diagnostics do not falsely certify art."""

from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.tileqa import diagnose_tiles, legal_neighbor


class TileQATest(unittest.TestCase):
    def test_wang_all_legal_pairs_and_generated_neighbors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGBA", (16, 16), (40, 100, 80, 255)).save(root / "atlas.png")
            report = diagnose_tiles(root / "atlas.png", root / "review", "wang16", 4)
            self.assertEqual(len(report["legal_seams"]), 128)
            self.assertTrue((root / "review/pairs_horizontal.png").is_file())
            self.assertTrue((root / "review/pairs_vertical.png").is_file())
            self.assertTrue(all("comparison" in seam for seam in report["legal_seams"]))
            self.assertEqual(report["status"], "needs_visual_review")
            masks = report["sampled_masks"]
            for y in range(8):
                for x in range(8):
                    if x < 7:
                        self.assertTrue(legal_neighbor(masks[y][x], masks[y][x+1], "horizontal"))
                    if y < 7:
                        self.assertTrue(legal_neighbor(masks[y][x], masks[y+1][x], "vertical"))

    def test_repeated_surface_reports_edge_discontinuity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = Image.new("RGBA", (4, 4), (0, 0, 0, 255))
            for y in range(4):
                image.putpixel((3, y), (255, 255, 255, 255))
            image.save(root / "tile.png")
            report = diagnose_tiles(root / "tile.png", root / "review")
            horizontal = next(seam for seam in report["legal_seams"] if seam["axis"] == "horizontal")
            self.assertGreater(horizontal["mean_edge_delta"], 100)
            self.assertEqual(report["status"], "needs_visual_review")

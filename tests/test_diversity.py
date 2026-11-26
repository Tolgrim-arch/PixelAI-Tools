"""Normalization must detect recoloring/padding without claiming originality."""
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

from pixelai.diversity import compare_silhouettes


class DiversityTest(unittest.TestCase):
    def test_padding_recolor_and_single_pixel_do_not_hide_similarity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = Image.new("RGBA", (32, 32))
            ImageDraw.Draw(original).polygon([(8, 4), (18, 4), (23, 25), (6, 25)], fill=(50, 120, 60, 255))
            original.save(root / "first.png")
            other = Image.new("RGBA", (48, 48))
            other.paste(original, (8, 8))
            ImageDraw.Draw(other).polygon([(16, 12), (26, 12), (31, 33), (14, 33)], fill=(220, 80, 60, 255))
            other.putpixel((31, 31), (220, 80, 60, 255))
            other.save(root / "second.png")
            result = compare_silhouettes(root / "first.png", root / "second.png")
            self.assertGreater(result["direct_iou"], .90)
            self.assertIsNone(result["approval"])

    def test_empty_silhouette_is_not_a_match(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.png"
            Image.new("RGBA", (8, 8)).save(path)
            with self.assertRaises(ValueError):
                compare_silhouettes(path, path)

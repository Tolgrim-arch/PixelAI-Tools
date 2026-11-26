"""Rejected visuals cannot gain another review by renaming or metadata edits."""

from pathlib import Path
import tempfile
import unittest

from PIL import Image, PngImagePlugin

from pixelai.revisions import check_rejected_revision, construction_identity


class RevisionTest(unittest.TestCase):
    def test_rename_metadata_and_padding_do_not_hide_rejected_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = Image.new("RGBA", (8, 8))
            image.paste(Image.new("RGBA", (4, 4), (50, 140, 70, 255)), (2, 2))
            image.save(root / "first.png")
            previous = construction_identity(root, {"image_path": "first.png"})
            padded = Image.new("RGBA", (16, 16))
            padded.paste(image, (4, 4))
            info = PngImagePlugin.PngInfo()
            info.add_text("claim", "brand new")
            padded.save(root / "renamed.png", pnginfo=info)
            candidate = construction_identity(root, {"image_path": "renamed.png"})
            with self.assertRaisesRegex(ValueError, "Unchanged rejected"):
                check_rejected_revision(candidate, [{"identity": previous, "defects": {"readability": {}}}])

    def test_runtime_only_repairs_are_allowed_only_for_technical_defects(self):
        previous = {"content_sha256": "pixels", "revision_sha256": "old-runtime"}
        repaired = {"content_sha256": "pixels", "revision_sha256": "new-runtime"}
        check_rejected_revision(repaired, [{"identity": previous, "defects": {"game_readiness": {}}}])
        with self.assertRaisesRegex(ValueError, "changed pixels"):
            check_rejected_revision(repaired, [{"identity": previous, "defects": {"materials": {}}}])

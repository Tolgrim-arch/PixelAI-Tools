"""Review packets bind actual frames without leaking author/peer arguments."""

from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.evidence import bind_evidence
from pixelai.review_packet import prepare_packet


class ReviewPacketTest(unittest.TestCase):
    def test_native_and_zoom_views_are_reproducible_and_artifact_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGBA", (8, 8), (40, 120, 70, 255)).save(root / "sprite.png")
            construction = {"image_path": "sprite.png", "evidence": bind_evidence(root, [{"path": "sprite.png"}]),
                            "author_justification": "This is excellent", "other_review": {"score": 4}}
            contract = {"category": "item", "native_size": [8, 8], "art_direction": "Clear shape", "functional_requirements": []}
            packet = prepare_packet(root, contract, construction, "art_review")
            self.assertEqual(packet, prepare_packet(root, contract, construction, "art_review"))
            self.assertEqual([view["zoom"] for view in packet["views"]], [1, 4])
            self.assertEqual(packet["observation_status"], "not_attested")
            self.assertNotIn("author_justification", packet)
            self.assertNotIn("other_review", packet)
            with Image.open(root / packet["views"][1]["path"]) as image:
                self.assertEqual(image.size, (32, 32))
            (root / packet["views"][0]["path"]).write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "integrity"):
                prepare_packet(root, contract, construction, "art_review")

"""Managed contracts reject empty promises and self-review."""
import unittest
import json
from pathlib import Path
import tempfile

from PIL import Image

from pixelai.production_contracts import validate_submission


class ProductionContractsTest(unittest.TestCase):
    def test_construction_cannot_claim_unrelated_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Image.new("RGBA", (4, 4), (0, 255, 0, 255)).save(root / "sprite.png")
            spec = {"width": 4, "height": 4, "style": "lineless", "ops": [{"op": "rect", "x": 0, "y": 0, "w": 4, "h": 4, "color": "#ff0000"}]}
            (root / "source.json").write_text(json.dumps(spec))
            data = {"source_path": "source.json", "image_path": "sprite.png", "evidence": [{"path": "source.json"}, {"path": "sprite.png"}]}
            with self.assertRaisesRegex(ValueError, "does not match"):
                validate_submission("construction", data, {}, root)
            spec["ops"][0]["color"] = "#00ff00"
            (root / "source.json").write_text(json.dumps(spec))
            validate_submission("construction", data, {}, root)

    def test_invalid_contract_and_duplicate_proposals(self):
        with self.assertRaises(ValueError):
            validate_submission("contract", {"category": "item", "native_size": [True, 32]}, {})
        proposals = [{"id": str(i), "structure": "Same body"} for i in range(6)]
        with self.assertRaisesRegex(ValueError, "distinct"):
            validate_submission("alternatives", {"proposals": proposals, "selected_id": "0"}, {})

    def test_self_review_is_not_accepted(self):
        with self.assertRaisesRegex(ValueError, "different context"):
            validate_submission("art_review", {"context_id": "AUTHOR", "author_context_id": "author"}, {})

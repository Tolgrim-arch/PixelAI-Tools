"""Review gates are evidence workflow tests, not an artistic quality benchmark."""

import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, PngImagePlugin
from pixelai.cli import main
from pixelai.quality import CRITERIA, assess_artifact, record_assessment, review_template


class CommercialReviewTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.image = self.root / "test.png"
        self.save(self.image)

    def save(self, path, size=16, offset=4, color=(100, 150, 200, 255), metadata=None):
        image = Image.new("RGBA", (size, size))
        for y in range(offset, offset + 5):
            for x in range(offset, offset + 4):
                image.putpixel((x, y), color)
        image.save(path, pnginfo=metadata)

    def attestation(self):
        review = review_template(self.image)
        review["generated_by"], review["reviewed_by"] = "generator", "independent-reviewer"
        review["comparison_reference"] = {
            "name": "Synthetic premium reference",
            "url": "https://example.com/reference",
            "notes": "Synthetic workflow test only; a real review must compare visible qualities",
        }
        review["inspection"] = {"native_resolution": True, "integer_zoom": 3}
        for name in CRITERIA:
            review["criteria"][name] = {"decision": "pass", "evidence": f"Synthetic test attestation for {name}; not real art approval"}
        return review

    def test_clean_metrics_alone_never_approve(self):
        assessment = assess_artifact(self.image)
        self.assertEqual(assessment["status"], "needs_review")
        self.assertFalse(assessment["commercial_ready"])
        self.assertEqual(set(assessment["pending"]), set(CRITERIA))

    def test_each_of_eleven_criteria_is_required(self):
        review = self.attestation()
        self.assertEqual(assess_artifact(self.image, review)["status"], "approved")
        for criterion in CRITERIA:
            with self.subTest(criterion=criterion):
                missing = copy.deepcopy(review)
                del missing["criteria"][criterion]
                self.assertFalse(assess_artifact(self.image, missing)["commercial_ready"])
                missing["criteria"][criterion] = {"decision": "fail", "evidence": "Visible defect"}
                self.assertEqual(assess_artifact(self.image, missing)["status"], "rejected")

    def test_no_self_approval_or_empty_evidence(self):
        review = self.attestation()
        review["reviewed_by"] = " GENERATOR "
        self.assertEqual(assess_artifact(self.image, review)["status"], "rejected")
        review = self.attestation()
        review["criteria"]["professional_quality"]["evidence"] = ""
        self.assertEqual(assess_artifact(self.image, review)["status"], "needs_review")

    def test_named_professional_reference_is_required(self):
        review = self.attestation()
        review["comparison_reference"] = {"name": "", "url": "", "notes": ""}
        self.assertEqual(assess_artifact(self.image, review)["status"], "needs_review")
        review["comparison_reference"] = {"name": "Pack", "url": "local-file", "notes": "Compared at 1x"}
        self.assertEqual(assess_artifact(self.image, review)["status"], "rejected")

    def test_changed_artifact_invalidates_review(self):
        review = self.attestation()
        self.save(self.image, color=(50, 70, 90, 255))
        assessment = assess_artifact(self.image, review)
        self.assertEqual(assessment["status"], "rejected")
        self.assertIn("stale", assessment["failures"][0])

    def test_rejected_pixels_survive_filename_metadata_and_padding_changes(self):
        rejection = assess_artifact(self.image)
        rejection["status"] = "rejected"
        ledger = self.root / "catalog.json"
        record_assessment(ledger, self.image, rejection)
        catalog = json.loads(ledger.read_text())
        for size, offset in ((16, 4), (24, 8)):
            target = self.root / f"renamed-{size}.png"
            metadata = PngImagePlugin.PngInfo()
            metadata.add_text("note", "supposedly new")
            self.save(target, size, offset, metadata=metadata)
            assessment = assess_artifact(target, catalog=catalog)
            self.assertEqual(assessment["status"], "rejected")
            self.assertIn("previously rejected", assessment["failures"][0])

    def test_contract_and_distinct_four_views_are_checked(self):
        review = self.attestation()
        review["contract"]["required_views"] = ["down", "up", "left", "right"]
        self.assertEqual(assess_artifact(self.image, review)["status"], "rejected")
        review["contract"]["views"] = [
            {"name": name, "x": 3, "y": 3, "w": 8, "h": 8} for name in review["contract"]["required_views"]]
        assessment = assess_artifact(self.image, review)
        self.assertTrue(any("identical" in message for message in assessment["failures"]))
        review["contract"]["width"] = 24
        self.assertTrue(any("dimensions" in m for m in assess_artifact(self.image, review)["failures"]))

    def test_invalid_view_coordinates_are_rejected(self):
        review = self.attestation()
        review["contract"]["views"] = [{"name": "front", "x": 10, "y": 10, "w": 16, "h": 16}]
        with self.assertRaisesRegex(ValueError, "outside"):
            assess_artifact(self.image, review)

    def test_cli_status_codes_template_and_append_only_ledger(self):
        target = self.root / "review.json"
        ledger = self.root / "catalog.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["qa", str(self.image), "--template", str(target)]), 2)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["qa", str(self.image), "--template", str(target)]), 1)
        target.write_text(json.dumps(self.attestation()))
        args = ["qa", str(self.image), "--review", str(target), "--catalog", str(ledger), "--record"]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args), 0)
            review = self.attestation()
            review["criteria"]["readability"] = {"decision": "fail", "evidence": "Unrecognizable silhouette"}
            target.write_text(json.dumps(review))
            self.assertEqual(main(args), 1)
            target.write_text(json.dumps(self.attestation()))
            self.assertEqual(main(args), 1)
        self.assertEqual([e["status"] for e in json.loads(ledger.read_text())["entries"]],
                         ["approved", "rejected", "rejected"])

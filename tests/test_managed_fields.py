"""Managed sources reject silent inventions throughout nested operations."""

import unittest

from pixelai.schema import format_op_guide, lint_op_fields, validate_managed_fields
from pixelai.runner import run_frames
import json
from pathlib import Path
import tempfile


class ManagedFieldsTest(unittest.TestCase):
    def test_invented_anatomy_is_rejected_and_real_controls_are_discoverable(self):
        operation = {"op": "char_rig", "anatomy_variation": "stocky"}
        self.assertTrue(lint_op_fields(operation))
        with self.assertRaisesRegex(ValueError, "anatomy_variation"):
            validate_managed_fields({"ops": [operation]})
        validate_managed_fields({"ops": [{"op": "char_rig", "outfit": "coat", "hair_style": "crop", "skin": "#eebb88"}]})
        self.assertIn("outfit", format_op_guide("char_rig"))

    def test_nested_parts_frames_and_postprocessing_are_checked(self):
        for spec in (
            {"frames": [{"ops": [{"op": "nature_rig", "trunck_color": "#885533"}]}]},
            {"ops": [{"op": "assembly", "parts": [{"ops": [{"op": "ui_rig", "ornamentation_magic": True}]}]}]},
            {"defs": {"shape": {"post": [{"op": "scale", "faktor": 2}]}}},
        ):
            with self.assertRaises(ValueError):
                validate_managed_fields(spec)

    def test_palette_aliases_and_definition_names_are_not_operations(self):
        validate_managed_fields({"palette": {"ops": "#448855"}, "defs": {"ops": {"width": 4, "height": 4,
                                "ops": [{"op": "pixel", "x": 0, "y": 0, "color": "ops"}]}}})

    def test_fresh_generation_checks_imported_definitions(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "library.json"
            source.write_text(json.dumps({"defs": {"reused": {"width": 4, "height": 4,
                              "ops": [{"op": "load_png", "path": "old.png"}]}}}))
            with self.assertRaisesRegex(ValueError, "fresh generation forbids"):
                run_frames({"width": 8, "height": 8, "fresh": True, "imports": [str(source)], "ops": []})

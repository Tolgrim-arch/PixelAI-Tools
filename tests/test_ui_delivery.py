"""UI delivery cannot pass with missing slices, small content or relabeled states."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.cli import main
from pixelai.delivery import verify_delivery,validate_delivery
from pixelai.ui_composition import STATES


class UIDeliveryTest(unittest.TestCase):
    def test_exported_states_geometry_and_content_requirements(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = Path(__file__).resolve().parents[1]/"specs/ui_states.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["render",str(source),"-o",str(root/"states.png"),"--columns","3","--manifest",str(root/"states.json")]),0)
            delivery = json.loads((source.parent/"ui_delivery.json").read_text())
            self.assertEqual(delivery["states"],list(STATES))
            report = verify_delivery(root/"states.json",delivery)
            self.assertEqual(report["ui_checks"]["status"],"checked")
            self.assertEqual(len(report["ui_checks"]["trials"]),12)
            from pixelai.production_contracts import validate_submission
            (root/"source.json").write_text(source.read_text())
            submission = {"source_path":"source.json","image_path":"states.png","manifest_path":"states.json",
                          "evidence":[{"path":name} for name in ("source.json","states.png","states.json")]}
            validate_submission("construction",submission,{"contract":{"native_size":[96,48],"delivery":delivery}},root)
            self.assertEqual(submission["delivery_verification"]["ui_checks"]["status"],"checked")
            with self.assertRaisesRegex(ValueError,"minimum"):
                verify_delivery(root/"states.json",{**delivery,"ui":{**delivery["ui"],"content_min":[100,20]}})
            with self.assertRaisesRegex(ValueError,"minimum"):
                validate_submission("construction",submission,{"contract":{"native_size":[96,48],"delivery":{**delivery,"ui":{**delivery["ui"],"content_min":[100,20]}}}},root)
            data = json.loads((root/"states.json").read_text())
            data["frames"][1]["state"] = "normal"
            (root/"states.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"state must match"):
                verify_delivery(root/"states.json",delivery)
            data["frames"][1]["state"] = "hover"
            original_ui = data["frames"][0].pop("ui")
            (root/"states.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"slice contract"):
                verify_delivery(root/"states.json",delivery)
            data["frames"][0]["ui"] = original_ui
            data["frames"][1]["ui"]["content"]["min"][0] += 1
            (root/"states.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"geometry must remain stable"):
                verify_delivery(root/"states.json",delivery)
            data["frames"][1]["ui"]["content"]["min"][0] -= 1
            with Image.open(root/"states.png") as image:
                texture = image.convert("RGBA")
            texture.paste(texture.crop((0,0,96,48)),(96,0))
            texture.save(root/"states.png")
            data["texture_sha256"] = hashlib.sha256((root/"states.png").read_bytes()).hexdigest()
            (root/"states.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"normal/hover.*identical"):
                verify_delivery(root/"states.json",delivery)

    def test_invalid_ui_requirements(self):
        for options in ({},{"target_sizes":[[0,10]]},{"target_sizes":[[64,32],[64,32]]},
                        {"target_sizes":[[64,32]],"content_min":[True,8]},
                        {"target_sizes":[[64,32]],"distinct_states":True},
                        {"target_sizes":[[64,32]],"magic":1}):
            with self.subTest(options=options),self.assertRaises(ValueError):
                validate_delivery({"ui":options})

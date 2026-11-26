"""Nine-slice evidence uses exported pixels and rejects malformed geometry."""

from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from pixelai.cli import main
from pixelai.nine_slice import check_ui,resize_ui,ui_contract,validate_ui
from pixelai.provenance import verify_construction
from pixelai.runner import run_spec
from pixelai.ui_composition import PROFILES,STATES


class NineSliceTest(unittest.TestCase):
    def test_all_profile_state_corners_preserve_content_clearance(self):
        for profile in PROFILES:
            for state in STATES:
                with self.subTest(profile=profile,state=state):
                    canvas = run_spec({"width":64,"height":40,"style":"lineless","ops":[
                        {"op":"ui_rig","w":64,"h":40,"state":state,"composition":{"profile":profile}}]})
                    contract = ui_contract(canvas.attachments)
                    image = Image.new("RGBA",(64,40))
                    image.putdata(canvas.pixels)
                    for size in ((48,32),(96,48),(128,72)):
                        resized,report = resize_ui(image,contract,size)
                        self.assertTrue(report["fixed_corners_preserved"])
                        content = report["content"]
                        crop = resized.crop((*content["min"],*content["max"]))
                        colors = set(getattr(crop,"get_flattened_data",crop.getdata)())
                        self.assertEqual(len(colors),1)

    def test_export_transforms_provenance_and_atomic_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = {"asset_id":"menu","width":64,"height":40,"style":"lineless","runtime":{"derive":"structure"},
                    "ops":[{"op":"ui_rig","w":64,"h":40,"state":"focus","composition":{"profile":"header"}}],
                    "post":[{"op":"pad","size":2},{"op":"scale","factor":2}]}
            (root/"source.json").write_text(json.dumps(spec))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["render",str(root/"source.json"),"-o",str(root/"menu.png"),"--manifest",str(root/"menu.json")]),0)
            submission = {"source_path":"source.json","image_path":"menu.png","manifest_path":"menu.json",
                          "evidence":[{"path":name} for name in ("source.json","menu.png","menu.json")]}
            verify_construction(root,submission,[136,88])
            data = json.loads((root/"menu.json").read_text())
            self.assertEqual(data["frames"][0]["ui"]["bounds"],{"min":[4,4],"max":[132,84]})
            report = check_ui(root/"menu.json","0",[[160,96],[192,112]],root/"review")
            self.assertEqual(report["status"],"needs_visual_review")
            self.assertTrue(all(trial["fixed_corners_preserved"] for trial in report["trials"]))
            self.assertTrue((root/"review/target_00_4x.png").exists())
            with self.assertRaises(ValueError):
                check_ui(root/"menu.json","0",[[10,10]],root/"failed")
            self.assertFalse((root/"failed").exists())
            data["frames"][0]["ui"]["content"]["min"][0] += 2
            (root/"menu.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"UI contract does not match"):
                verify_construction(root,submission)

    def test_invalid_caps_ornaments_and_content(self):
        canvas = run_spec({"width":64,"height":40,"ops":[{"op":"ui_rig","w":64,"h":40,"composition":{"profile":"brackets"}}]})
        original = ui_contract(canvas.attachments)
        for path,value in (("bounds",{"min":[0,0],"max":[100,40]}),("cuts",{"min":[0,8],"max":[56,32]}),
                           ("content",{"min":[5,5],"max":[59,35]})):
            bad = deepcopy(original)
            bad[path] = value
            with self.assertRaises(ValueError):
                validate_ui(bad,64,40)
        bad = deepcopy(original)
        bad["anchors"][0]["point"] = [32,20]
        with self.assertRaisesRegex(ValueError,"fixed corner"):
            validate_ui(bad,64,40)
